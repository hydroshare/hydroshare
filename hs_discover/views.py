from django.shortcuts import render
from django.views.generic import TemplateView


class AtlasSearchView(TemplateView):

    def get(self, request, *args, **kwargs):
        target_origin = request.scheme + "://" + request.get_host()
        iframe_src = target_origin + "/discover/"
        if request.META.get('QUERY_STRING'):
            iframe_src += "?" + request.META['QUERY_STRING']
        context = {"targetOrigin": target_origin, "iframeSrc": iframe_src}
        return render(request, 'pages/search.html', context)


class AtlasLandingView(TemplateView):

    def get(self, request, *args, **kwargs):
        import json
        from hs_core.hydroshare.utils import get_resource_by_shortkey
        from hs_core.models import get_access_object
        from hs_core.enums import RelationTypes

        target_origin = request.scheme + "://" + request.get_host()
        shortkey = kwargs.get('shortkey', '')

        # Mirror the legacy Mezzanine page processor: bump the view count when
        # the resource landing page is requested. The Vue app inside the iframe
        # only renders metadata via API calls, so this is the only place where
        # the visit is recorded.
        resource = get_resource_by_shortkey(shortkey)
        resource.update_view_count()

        # Pop just_created / just_copied from the session, mirroring the legacy
        # page processor — these are set by the create/copy/new-version flows
        # and must be consumed on first read so they don't reappear on later
        # visits to the same resource.
        just_created = bool(request.session.pop('just_created', False)) if request else False
        just_copied = bool(request.session.pop('just_copied', False)) if request else False

        title_value = resource.metadata.title.value if resource.metadata.title else ""
        try:
            missing_metadata = list(
                resource.metadata.get_required_missing_elements()
            )
        except Exception:
            missing_metadata = []
        try:
            recommended_missing = list(
                resource.metadata.get_recommended_missing_elements()
            )
        except Exception:
            recommended_missing = []
        try:
            has_required_content_files = bool(resource.has_required_content_files)
        except Exception:
            has_required_content_files = True
        try:
            is_replaced_by = resource.get_relation_version_res_url(RelationTypes.isReplacedBy) or None
        except Exception:
            is_replaced_by = None
        try:
            is_version_of = resource.get_relation_version_res_url(RelationTypes.isVersionOf) or None
        except Exception:
            is_version_of = None

        alerts = {
            "justCreated": just_created,
            "justCopied": just_copied,
            "missingMetadata": missing_metadata,
            "recommendedMissing": recommended_missing,
            "hasRequiredContentFiles": has_required_content_files,
            "isUntitled": (title_value or "").strip().lower() == "untitled resource",
            "isReplacedBy": is_replaced_by,
            "isVersionOf": is_version_of,
            "reviewPending": bool(resource.raccess.review_pending),
            "isPublished": bool(resource.raccess.published),
            "displayName": (resource.display_name or resource.resource_type or "resource").lower(),
        }

        # Build the owners payload the same shape the legacy left-header
        # template feeds to its Vue widget (USERS_JSON). The iframe-hosted
        # landing page picks this up via postMessage in atlas.html.
        owners = []
        for owner in resource.raccess.owners.all():
            owner.can_undo = False
            owner.viewable_contributions = 0
            owners.append(get_access_object(owner, "user", "owner"))

        # The schema.org dataset_metadata.json that the Vue app reads doesn't
        # carry hs_user_id / is_active_user / relative_uri — those are needed
        # to surface the "View HydroShare profile" link in the author dropdown,
        # so we side-channel them by `name` for the Vue side to merge.
        creator_profiles = [
            {
                "name": c.get("name"),
                "hs_user_id": c.get("hs_user_id"),
                "is_active_user": c.get("is_active_user"),
                "relative_uri": c.get("relative_uri"),
                "identifiers": c.get("identifiers") or {},
            }
            for c in resource.cached_metadata.get("creators", [])
            if c.get("name")
        ]

        context = {
            "targetOrigin": target_origin,
            "iframeSrc": "{}/discover/resource-v2/{}?viewCount={}&downloadCount={}".format(
                target_origin, shortkey, resource.view_count, resource.download_count
            ),
            "page_title": resource.metadata.title.value if resource.metadata.title else shortkey,
            "owners_json": json.dumps(owners),
            "creator_profiles_json": json.dumps(creator_profiles),
            "alerts_json": json.dumps(alerts),
        }
        return render(request, 'hs_discover/atlas.html', context)
