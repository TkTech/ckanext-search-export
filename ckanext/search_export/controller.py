import json
import urllib.parse

import ckan.plugins.toolkit as toolkit
import ckan.lib.base as base
import ckan.lib.jobs as jobs

from ckan.common import g

from ckanext.search_export.tasks import export


def search_export_create():
    """
    View to create a search export job.
    """
    if not g.userobj:
        return base.abort(403, "You must be logged in to access this page.")

    q = toolkit.request.form.get("q")
    if q is None:
        return toolkit.abort(400, "Missing required parameter: q")

    fields: str | None = toolkit.request.form.get("fields")
    if not fields:
        return toolkit.abort(400, "Missing required parameter: fields")

    fields: list[tuple[str, str]] = json.loads(urllib.parse.unquote(fields))

    job: jobs.Job = jobs.enqueue(
        export.export_search_results,
        [g.userobj.name],
        {
            "q": q,
            "fields": fields,
        },
    )

    return toolkit.redirect_to(
        "search_export.search_export_status",
        job_id=job.id,
    )


def search_export_status(job_id: str):
    """
    View to check the status of a search export job.

    :param job_id: The ID of the job to check.
    """
    if not g.userobj:
        return base.abort(403, "You must be logged in to access this page.")

    job = jobs.job_from_id(job_id)
    if job.args[0] != g.userobj.name:
        return toolkit.abort(403, "You do not have permission to access this job.")

    return toolkit.render(
        "search_export/search_export.html",
        extra_vars={
            "job": job,
            "result": job.latest_result(),
        },
    )
