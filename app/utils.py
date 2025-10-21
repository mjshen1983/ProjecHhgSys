from typing import Dict, Any


def build_base_context(request) -> Dict[str, Any]:
    session = request.session
    return {
        'display_name': session.get('display_name'),
        'permission_code': session.get('permission_code', 'member'),
        'can_manage_users': session.get('can_manage_users', False),
        'can_manage_permissions': session.get('can_manage_permissions', False),
        'can_manage_projects': session.get('can_manage_projects', False),
        'can_manage_tasks': session.get('can_manage_tasks', False),
        'can_view_all_tasks': session.get('can_view_all_tasks', False),
        'can_edit_all_tasks': session.get('can_edit_all_tasks', False),
        'department_id': session.get('department_id'),
    }
