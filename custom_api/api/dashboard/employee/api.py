from custom_api.utils.response import send_old_response
import frappe
from frappe.utils import flt, nowdate , getdate
from datetime import date


@frappe.whitelist(allow_guest=False, methods=["GET"])
def employee_dashboard(employee_id=None):
    try:

        if not employee_id:
            return send_old_response(
                status="error",
                message="employee_id is required",
                data=None,
                status_code=400,
                http_status=400,
            )

        if not frappe.db.exists("Employee", employee_id):
            return send_old_response(
                status="error",
                message=f"Employee '{employee_id}' not found.",
                data=None,
                status_code=404,
                http_status=404,
            )

        emp = frappe.db.get_value(
            "Employee",
            employee_id,
            [
                "name",              
                "employee_number",   
                "first_name",
                "middle_name",
                "last_name",
                "employee_name",     
                "image",            
                "date_of_joining",
                "leave_approver",  
                "expense_approver",
                "shift_request_approver",
            ],
            as_dict=True,
        )


        leave_approver_name = None
        if emp.leave_approver:
            leave_approver_name = frappe.db.get_value(
                "User", emp.leave_approver, "full_name"
            )

        expense_approver_name = None
        if emp.expense_approver:
            expense_approver_name = frappe.db.get_value(
                "User", emp.expense_approver,"full_name"
            )

        shift_request_approver_name = None
        if emp.shift_request_approver:
            shift_request_approver_name = frappe.db.get_value(
                "User", emp.shift_request_approver,"full_name"
            )


        employee_details = {
            "employeeId":          emp.name,
            "employeeNumber":      emp.employee_number,
            "firstName":           emp.first_name,
            "middleName":          emp.middle_name,
            "lastName":            emp.last_name,
            "employeeName":        emp.employee_name,
            "profilePhoto":        emp.image,
            "dateOfJoining":       str(emp.date_of_joining) if emp.date_of_joining else None,
            "leaveApproverId":     emp.leave_approver,
            "leaveApproverName":   leave_approver_name,
            "expenseApproverName": expense_approver_name,
            "shiftApproverName" :  shift_request_approver_name,
        }

        today = nowdate()

        allocations = frappe.db.get_all(
            "Leave Allocation",
            filters={
                "employee":  employee_id,
                "docstatus": 1,
                "from_date": ["<=", today],
                "to_date":   [">=", today],
            },
            fields=["leave_type", "total_leaves_allocated" ],
        )


        applications = frappe.db.get_all(
            "Leave Application",
            filters={
                "employee":  employee_id,
                "docstatus": 1,
                "status":    "Approved",
            },
            fields=["leave_type", "total_leave_days"],
        )

  
        leave_map = {}

        for alloc in allocations:
            lt = alloc.leave_type
            if lt not in leave_map:
                leave_map[lt] = {"allocated": 0.0, "used": 0.0}
            leave_map[lt]["allocated"] += flt(alloc.total_leaves_allocated)

        for app in applications:
            lt = app.leave_type
            if lt not in leave_map:
                leave_map[lt] = {"allocated": 0.0, "used": 0.0}
            leave_map[lt]["used"] += flt(app.total_leave_days)

        leave_types_list = []
        for leave_type, vals in leave_map.items():
            allocated = vals["allocated"]
            used      = vals["used"]
            remaining = max(allocated - used, 0.0)
            leave_types_list.append({
                "leaveType": leave_type,
                "allocated": allocated,
                "used":      used,
                "remaining": remaining,
            })

        leave_types_list.sort(key=lambda x: x["leaveType"])



        total_allocated = sum(lt["allocated"] for lt in leave_types_list)
        total_used      = sum(lt["used"]      for lt in leave_types_list)
        total_remaining = max(total_allocated - total_used, 0.0)

        leave_balance = {
            "asOfDate":       today,
            "totalAllocated": total_allocated,
            "totalUsed":      total_used,
            "totalRemaining": total_remaining,
            "leaveTypes":     leave_types_list,
        }

        checkins = frappe.db.get_all(
            "Employee Checkin",
            filters= {
                "employee":employee_id,
            },
            fields=["log_type","time"],
            order_by="time asc"
        )
        current_in_time = None
        current_out_time = None
        in_time = None
        out_time = None
        for row in checkins:
            if row.get("log_type") == "IN":
                current_in_time = row.get("time")
                current_out_time = None
            elif row.log_type == "OUT" and current_in_time:
                current_out_time = row.time

        if current_out_time:
            in_time = current_in_time
            out_time = current_out_time
        else:
            in_time = current_in_time
            out_time = None

    
        attendance_data = {
            "asofDate":today,
            "inTime": in_time,
            "outTime": out_time,
        }

        # appraisal = frappe.db.get_all(
        #     "Appraisal Cycle",
        #     filters={
                    
        #     },
        #     fields=["name"]
        # )

        holidays = frappe.db.get_all(
            "Holiday List Assignment",
            filters={
                "assigned_to":employee_id
            },
            fields=["holiday_list"]
        )
        
        upcoming_holiday_list = []
        for holiday in holidays:
            temp = frappe.db.get_all(
                                        "Holiday",
                                        filters={
                                            "parent": holiday.holiday_list,
                                            "parenttype": "Holiday List",
                                            "holiday_date": [">=", today],
                                        },
                                            fields=["holiday_date", "description"],
                                            order_by="holiday_date asc",
                                            limit=4,
                                        )        
            for h in temp:
                if h:
                    upcoming_holiday_list.append({"date": str(h.holiday_date), "description": h.description or ""})
        
        upcoming_holidays = {
        "upcoming": upcoming_holiday_list if upcoming_holiday_list else None,
        }
 
        birthdays = frappe.db.get_all(
            "Employee",
            filters={
                "status":"Active",
                "date_of_birth": ["is", "set"]
            },
            fields=["employee_name","date_of_birth"],
        )

        today = getdate(nowdate())
        upcoming_birthdays_list = []

        for emp in birthdays:
            dob = getdate(emp.date_of_birth)
            next_birthday=date(
                today.year,
                dob.month,
                dob.day    
            )

            if next_birthday < today:
                next_birthday = date(
                today.year + 1,
                dob.month,
                dob.day
            )
            
            days_left = (next_birthday - today).days

            upcoming_birthdays_list.append({
            "employeeName": emp.employee_name,
            "dateOfBirth": str(emp.date_of_birth),
            "daysLeft": days_left
            })

        upcoming_birthdays_list.sort(key=lambda x: x["daysLeft"])

        upcoming_birthdays = {
        "upcoming": upcoming_birthdays_list[:4]
        }



        return send_old_response(
            status="success",
            message="Employee dashboard retrieved successfully.",
            data={
                "employeeDetails": employee_details,
                "leaveBalance":    leave_balance,
                "checkins":        attendance_data,
                "holidays":        upcoming_holidays,
                "birthdays":       upcoming_birthdays
            },
            status_code=200,
            http_status=200,
        )

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Employee Dashboard API Error")
        return send_old_response(
            status="error",
            message=f"Error retrieving employee dashboard: {str(e)}",
            data=None,
            status_code=500,
            http_status=500,
        )