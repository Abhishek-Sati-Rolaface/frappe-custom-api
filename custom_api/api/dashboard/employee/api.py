from custom_api.utils.response import send_old_response
import frappe
from frappe.utils import flt, nowdate


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
                "holiday_list",     
            ],
            as_dict=True,
        )


        leave_approver_name = None
        if emp.leave_approver:
            leave_approver_name = frappe.db.get_value(
                "User", emp.leave_approver, "full_name"
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
            "holidayList":         emp.holiday_list,
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

        # B-2: Approved leave applications (leaves taken)
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

        # B-5: Grand totals across all leave types
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


        return send_old_response(
            status="success",
            message="Employee dashboard retrieved successfully.",
            data={
                "employeeDetails": employee_details,
                "leaveBalance":    leave_balance,
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