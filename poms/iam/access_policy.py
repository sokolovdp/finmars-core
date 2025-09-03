import importlib
import logging
from dataclasses import asdict, dataclass, field

from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.db.models import prefetch_related_objects
from pyparsing import infixNotation, opAssoc
from rest_framework import permissions

from .exceptions import AccessPolicyException
from .models import ResourceGroup
from .parsing import BoolAnd, BoolNot, BoolOperand, BoolOr, ConditionOperand
from .utils import action_statement_into_object

_l = logging.getLogger("poms.iam")


class AnonymousUser:
    def __init__(self):
        self.pk = None
        self.is_anonymous = True
        self.is_staff = False
        self.is_superuser = False


class AccessEnforcement:
    _action: str
    _allowed: bool

    def __init__(self, action: str, allowed: bool):
        self._action = action
        self._allowed = allowed

    @property
    def action(self) -> str:
        return self._action

    @property
    def allowed(self) -> bool:
        return self._allowed


@dataclass
class Statement:
    principal: list[str] | str
    action: list[str] | str
    effect: str = "deny"  # allow, deny
    condition: list[str] | str = field(default_factory=list)
    condition_expression: list[str] | str = field(default_factory=list)

    def __post_init__(self):
        if self.effect not in ("allow", "deny"):
            permitted = ("allow", "deny")

            raise RuntimeError(f"effect must be one of {permitted}")


class AccessPolicy(permissions.BasePermission):
    statements: list[dict | Statement] = []
    field_permissions: dict = {}
    id = None
    group_prefix = "group:"
    id_prefix = "id:"

    def has_permission(self, request, view) -> bool:
        if not request.user.is_authenticated:
            return False

        if request.user.is_superuser:
            return True

        if request.user.member and request.user.member.is_admin:
            return True

        return self.has_specific_permission(view, request)

    def has_object_permission(self, request, view, obj):
        if not request.user.is_authenticated:
            return False

        if request.user.is_superuser:
            return True

        if request.user.member and request.user.member.is_admin:
            return True

        # TODO Member entity itself has no owner, be careful if other entities have no owner
        if hasattr(obj, "owner"):
            # Check if the user is the owner
            if obj.owner == request.user.member:
                return True

        return self.has_specific_permission(view, request, obj)

    def has_specific_permission(self, view, request, obj=None):
        statements = self.get_policy_statements(request, view)

        action = self._get_invoked_action(view)
        user_arn = f"frn:finmars:users:member:{request.user.username}"  # Customize to suit your naming convention
        viewset_name = f"finmars:{view.__class__.__name__.replace('ViewSet', '')}"

        if not statements:
            request.permission_error_message = (
                f"User: {user_arn} is not authorized to perform: "
                f"{action} on resource: {viewset_name} because no access policy allows the '{action}' action."
            )

            return False

        allowed = self._evaluate_statements(statements, request, view, action, obj=None)
        request.access_enforcement = AccessEnforcement(action=action, allowed=allowed)

        _l.info("has_specific_permission.allowed %s", allowed)

        if not allowed:
            request.permission_error_message = (
                f"User: {user_arn} is not authorized to perform: "
                f"{action} on resource: {viewset_name} because no access policy allows the '{action}' action."
            )

            _l.info("permission_error_message %s", request.permission_error_message)

        return allowed

    def get_policy_statements(self, request, view) -> list[dict | Statement]:
        return self.statements

    def get_user_group_values(self, user) -> list[str]:
        if user.is_anonymous:
            return []

        prefetch_related_objects([user], "groups")
        return [g.name for g in user.groups.all()]

    @classmethod
    def scope_queryset(cls, request, qs):
        return qs.none()

    @classmethod
    def scope_fields(cls, request, fields: dict, instance=None) -> dict:
        return fields

    def _get_invoked_action(self, view) -> str:
        """
        If a CBV, the name of the method. If a regular function view,
        the name of the function.
        """
        if hasattr(view, "action"):
            if hasattr(view, "action_map"):
                return view.action or list(view.action_map.values())[0]
            return view.action

        elif hasattr(view, "__class__"):
            return view.__class__.__name__

        raise AccessPolicyException("Could not determine action of request")

    def _evaluate_statements(
        self,
        statements: list[dict | Statement],
        request,
        view,
        action: str,
        obj=None,
    ) -> bool:
        statements = self._normalize_statements(statements)

        matched = self._get_statements_matching_principal(request, statements)
        matched = self._get_statements_matching_action(request, view, action, matched)

        matched = self._get_statements_matching_conditions(
            request, view, action=action, statements=matched, is_expression=False
        )

        matched = self._get_statements_matching_conditions(
            request, view, action=action, statements=matched, is_expression=True
        )

        if obj is not None:
            matched = self._get_statements_matching_resource(request, view, action=action, statements=matched, obj=obj)

        denied = [_ for _ in matched if _["effect"].lower() != "allow"]

        # TODO IAM_SECURITY_VERIFY check approach
        #  if one deny cancels all access"
        _l.debug(f"len(matched) {len(matched)}  len(denied) {len(denied)}")

        return not (len(matched) == 0 or len(denied) > 0)

    def _normalize_statements(self, statements: list[dict | Statement]) -> list[dict]:
        normalized = []

        for statement in statements:
            if isinstance(statement, Statement):
                statement = asdict(statement)  # noqa: PLW2901

            # _l.debug(f"_normalize_statements.statement {statement} ")

            if isinstance(statement["principal"], str):
                statement["principal"] = [statement["principal"]]

            if isinstance(statement["action"], str):
                statement["action"] = [statement["action"]]

            if "condition" not in statement:
                statement["condition"] = []
            elif isinstance(statement["condition"], str):
                statement["condition"] = [statement["condition"]]

            if "condition_expression" not in statement:
                statement["condition_expression"] = []
            elif isinstance(statement["condition_expression"], str):
                statement["condition_expression"] = [statement["condition_expression"]]

            normalized.append(statement)

        return normalized

    @classmethod
    def _get_statements_matching_principal(cls, request, statements: list[dict]) -> list[dict]:
        user = request.user or AnonymousUser()
        user_roles = None
        matched = []

        for statement in statements:
            principals = statement["principal"]
            found = False

            if (
                "*" in principals
                or "admin" in principals
                and user.is_superuser
                or "staff" in principals
                and user.is_staff
                or "authenticated" in principals
                and not user.is_anonymous
                or "anonymous" in principals
                and user.is_anonymous
                or cls.id_prefix + str(user.pk) in principals
            ):
                found = True
            else:
                if not user_roles:
                    user_roles = cls().get_user_group_values(user)

                for user_role in user_roles:
                    if cls.group_prefix + user_role in principals:
                        found = True
                        break

            if found:
                matched.append(statement)

        return matched

    def _get_statements_matching_action(self, request, view, action: str, statements: list[dict]):
        """
        Filter statements and return only those that match the specified
        action.
        """
        matched = []
        SAFE_METHODS = ("GET", "HEAD", "OPTIONS")
        http_method = f"<method:{request.method.lower()}>"

        viewset_name = view.__class__.__name__.replace("ViewSet", "")

        _l.debug(f"_get_statements_matching_action.action {action} name {viewset_name.lower()}")
        # _l.info('_get_statements_matching_action.view %s' % view.__dict__)
        # _l.info('_get_statements_matching_action.self %s' % self)
        # _l.info('_get_statements_matching_action.request %s' % request)

        for statement in statements:
            for action_statement in statement["action"]:
                action_object = action_statement_into_object(action_statement)
                # _l.debug('_get_statements_matching_action.action_object %s' % action_object)

                if settings.SERVICE_NAME in action_object["service"]:
                    """
                    TODO IAM_SECURITY_VERIFY here is good place, it would work as intended because 
                    we have access to view
                    but in Field filter we do not have access to view so we compare with model.name
                    maybe its a problem, see  utils.py#get_allowed_resources

                    """

                    if viewset_name.lower() in action_object["viewset"]:
                        if (
                            action in action_object["action"]
                            or "*" in action_object["action"]
                            or http_method in action_object["action"]
                            or "<safe_methods>" in action_object["action"]
                            and request.method in SAFE_METHODS
                        ):
                            matched.append(statement)

        # _l.debug('_get_statements_matching_action.matched %s' % matched)

        return matched

    def _get_statements_matching_resource(self, request, view, action: str, statements: list[dict], obj) -> list[dict]:
        """
        Filters statements to find those that match the resource defined in each statement.
        If the resource is "*", it grants access to all objects.
        If specific resources are defined, it checks if obj.user_code matches one of them
        or is associated with a `ResourceGroup`.
        """
        matched_statements = []

        # Determine the content type of the object (e.g., "portfolios:portfolio")
        content_type = ContentType.objects.get_for_model(obj).app_label + ":" + obj.__class__.__name__.lower()

        # Construct the unique resource identifier for the object
        object_resource_identifier = f"frn:finmars:{content_type}:{obj.user_code}"

        for statement in statements:
            resources = statement.get("Resource", [])

            # Check if the resource list contains a `ResourceGroup`, and if so, expand it
            expanded_resources = set(resources)  # Start with a copy of original resources

            for resource in resources:
                if resource.startswith("frn:finmars:iam:resourcegroup:"):
                    # Extract the `user_code` for the ResourceGroup from the resource identifier
                    resource_group_code = resource.split(":")[-1]

                    try:
                        # Fetch the ResourceGroup and its assignments
                        resource_group = ResourceGroup.objects.get(user_code=resource_group_code)
                        assignments = resource_group.assignments.all()

                        # Add each assigned object's user_code to the expanded resources list
                        expanded_resources.update(
                            f"frn:finmars:{assignment.content_type.app_label}:{assignment.content_type.model}:{assignment.object_user_code}"
                            for assignment in assignments
                            if assignment.object_user_code
                        )

                    except ResourceGroup.DoesNotExist:
                        _l.warning(f"ResourceGroup with user_code {resource_group_code} does not exist.")
                        continue

            # Allow all if the original or expanded resource list contains "*"
            if "*" in expanded_resources:
                matched_statements.append(statement)
                continue

            # Check if the object's identifier matches any entry in the expanded resources
            if object_resource_identifier in expanded_resources:
                matched_statements.append(statement)

        return matched_statements

    def _get_statements_matching_conditions(
        self, request, view, *, action: str, statements: list[dict], is_expression: bool
    ):
        """
        Filter statements and only return those that match all of their
        custom context conditions; if no conditions are provided then
        the statement should be returned.
        """
        matched = []
        element_key = "condition_expression" if is_expression else "condition"

        for statement in statements:
            conditions = statement[element_key]

            if len(conditions) == 0:
                matched.append(statement)
                continue

            fails = 0

            boolOperand = BoolOperand()

            for condition in conditions:
                if is_expression:
                    check_cond_fn = lambda cond: self._check_condition(cond, request, view, action)  # noqa: E731

                    boolOperand.setParseAction(lambda token: ConditionOperand(token, check_cond_fn))  # noqa: B023

                    boolExpr = infixNotation(
                        boolOperand,
                        [
                            ("not", 1, opAssoc.RIGHT, BoolNot),
                            ("and", 2, opAssoc.LEFT, BoolAnd),
                            ("or", 2, opAssoc.LEFT, BoolOr),
                        ],
                    )

                    passed = bool(boolExpr.parseString(condition)[0])
                else:
                    passed = self._check_condition(condition, request, view, action)

                if not passed:
                    fails += 1
                    break

            if fails == 0:
                matched.append(statement)

        return matched

    def _check_condition(self, condition: str, request, view, action: str):
        """
        Evaluate a custom context condition; if method does not exist on
        the access policy class, then return False.
        Condition value can contain a value that is passed to method, if
        formatted as `<method_name>:<arg_value>`.
        """
        parts = condition.split(":", 1)
        method_name = parts[0]
        arg = parts[1] if len(parts) == 2 else None
        method = self._get_condition_method(method_name)

        if arg is not None:
            result = method(request, view, action, arg)
        else:
            result = method(request, view, action)

        if type(result) is not bool:
            raise AccessPolicyException(f"condition '{condition}' must return true/false, not {type(result)}")

        return result

    def _get_condition_method(self, method_name: str):
        if hasattr(self, method_name):
            return getattr(self, method_name)

        if hasattr(settings, "DRF_ACCESS_POLICY"):
            module_paths = settings.DRF_ACCESS_POLICY.get("reusable_conditions")

            if module_paths:
                if not isinstance(module_paths, str | list | tuple):
                    raise ValueError("Define 'resusable_conditions' as list, tuple or str")

                module_paths = [module_paths] if isinstance(module_paths, str) else module_paths

                for module_path in module_paths:
                    module = importlib.import_module(module_path)

                    if hasattr(module, method_name):
                        return getattr(module, method_name)

        raise AccessPolicyException(
            f"condition '{method_name}' must be a method on the access policy "
            f"or be defined in the 'reusable_conditions' module"
        )
