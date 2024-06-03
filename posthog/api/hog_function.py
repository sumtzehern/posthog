import structlog
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import serializers, viewsets
from rest_framework.serializers import BaseSerializer

from posthog.api.forbid_destroy_model import ForbidDestroyModel
from posthog.api.routing import TeamAndOrgViewSetMixin
from posthog.api.shared import UserBasicSerializer
from posthog.models.hog_functions.hog_function import HogFunction

logger = structlog.get_logger(__name__)


class HogFunctionMinimalSerializer(serializers.ModelSerializer):
    created_by = UserBasicSerializer(read_only=True)
    last_modified_by = UserBasicSerializer(read_only=True)

    class Meta:
        model = HogFunction
        fields = [
            "name",
            "description",
            "created_at",
            "created_by",
            "updated_at",
            "enabled",
            "hog",
            "filters",
        ]
        read_only_fields = fields


class HogFunctionSerializer(HogFunctionMinimalSerializer):
    class Meta:
        model = HogFunction
        fields = [
            "name",
            "description",
            "created_at",
            "created_by",
            "updated_at",
            "enabled",
            "hog",
            "bytecode",
            "bytecode_error",
            "inputs_schema",
            "inputs",
            "filters",
        ]
        read_only_fields = [
            "created_at",
            "created_by",
            "updated_at",
            "bytecode",
            "bytecode_error",
            "inputs_schema",
            "inputs",
            "filters",
        ]

    def validate(self, attrs):
        request = self.context["request"]
        team = self.context["get_team"]()

        attrs["team"] = team
        attrs["created_by"] = request.user
        attrs["last_modified_by"] = request.user

        attrs["team"] = team

    def create(self, validated_data: dict, *args, **kwargs) -> HogFunction:
        request = self.context["request"]
        validated_data["created_by"] = request.user
        return super().create(validated_data=validated_data)


class HogFunctionViewSet(TeamAndOrgViewSetMixin, ForbidDestroyModel, viewsets.ModelViewSet):
    scope_object = "INTERNAL"  # Keep internal until we are happy to release this GA
    queryset = HogFunction.objects.all()
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["id", "team", "created_by", "enabled"]

    def get_serializer_class(self) -> type[BaseSerializer]:
        return HogFunctionMinimalSerializer if self.action == "list" else HogFunctionSerializer

    # def safely_get_queryset(self, queryset) -> QuerySet:
    #     if not self.action.endswith("update"):
    #         # Soft-deleted notebooks can be brought back with a PATCH request
    #         queryset = queryset.filter(deleted=False)

    #     queryset = queryset.select_related("created_by", "last_modified_by", "team")
    #     if self.action == "list":
    #         queryset = queryset.filter(deleted=False)
    #         queryset = self._filter_list_request(self.request, queryset)

    #     order = self.request.GET.get("order", None)
    #     if order:
    #         queryset = queryset.order_by(order)
    #     else:
    #         queryset = queryset.order_by("-last_modified_at")

    #     return queryset

    # @action(methods=["GET"], url_path="activity", detail=True, required_scopes=["activity_log:read"])
    # def activity(self, request: Request, **kwargs):
    #     notebook = self.get_object()
    #     limit = int(request.query_params.get("limit", "10"))
    #     page = int(request.query_params.get("page", "1"))

    #     activity_page = load_activity(
    #         scope="Notebook",
    #         team_id=self.team_id,
    #         item_ids=[notebook.id, notebook.short_id],
    #         limit=limit,
    #         page=page,
    #     )
    #     return activity_page_response(activity_page, limit, page, request)
