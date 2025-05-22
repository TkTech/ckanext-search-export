import io
import csv
import secrets
import os.path
from tempfile import NamedTemporaryFile
from typing import Optional

from werkzeug.datastructures import FileStorage

import ckan.plugins.toolkit as toolkit
from ckan import authz
from ckan.lib.uploader import get_uploader, Upload


class EmptyResultError(Exception):
    """Exception raised when no results are found for the given query."""


def export_to_file(
    username: str,
    output: io.FileIO,
    *,
    q: Optional[str] = None,
    fields: Optional[list[tuple[str, str]]] = None,
    file_type: str = "csv",
    chunk_size: int = 1000,
):
    """
    Export search results to a file.

    :param username: The user who is performing the export.
    :param output: The file-like object to write the results to.
    :param q: A search query string.
    :param fields: A list of field filters to apply to the search results.
    :param file_type: The type of file to export to (e.g., 'csv').
    :param chunk_size: The number of rows to fetch in each chunk.
    """
    args = {
        "q": q,
        "facet": False,
        "fq_list": [f"{field}:{value}" for field, value in fields] if fields else [],
        "include_private": authz.is_sysadmin(username),
    }

    # Get a single search result to get the column headers and to ensure
    # there's at least one result. The IUploader interface will fail if the
    # result file is empty since it can't guess the mimetype.
    response = toolkit.get_action("package_search")(
        {"user": username},
        {**args, "start": 0, "rows": 1},
    )

    results = response.get("results", [])
    if not results:
        raise EmptyResultError("No results found for the given query.")

    columns = results[0].keys()

    # FileStorage expects a bytes-like object, while csv.DictWriter expects
    # a text-like object.
    encoded_wrapper = io.TextIOWrapper(
        output,
        encoding="utf-8",
        newline="",
    )

    writer = csv.DictWriter(encoded_wrapper, fieldnames=columns)
    writer.writeheader()

    # Paginate through the results in chunks.
    offset = 0
    while True:
        response = toolkit.get_action("package_search")(
            {"user": username},
            {
                **args,
                "start": offset,
                "rows": chunk_size,
            },
        )

        results = response.get("results", [])
        if not results:
            break

        writer.writerows(results)

        if len(results) < chunk_size:
            break

        offset += chunk_size

    # Prevent the wrapper from closing the underlying buffer.
    encoded_wrapper.detach()


def export_search_results(
    username: str,
    *,
    q: Optional[str] = None,
    fields: Optional[list[tuple[str, str]]] = None,
    file_type: str = "csv",
):
    """
    Export search results to a file and upload it using CKAN's configured
    file storage.

    :param username: The user who is performing the export.
    :param q: A search query string.
    :param fields: A list of field filters to apply to the search results.
    :param file_type: The type of file to export to (e.g., 'csv').
    """
    with NamedTemporaryFile(suffix=f".{file_type}") as tmp_file:
        try:
            export_to_file(
                username,
                tmp_file,
                q=q,
                fields=fields,
                file_type="csv",
            )
        except EmptyResultError:
            # TODO: Handle failure case.
            pass

        tmp_file.seek(0)

        filename = f"{secrets.token_urlsafe(128)}.{file_type}"
        storage = FileStorage(
            tmp_file,
            filename=filename,
            content_type="text/csv",
        )

        # This entire IUploader interface is exceptionally hacky.
        data_dict = {"url": None, "file": storage}
        uploader = get_uploader("search_export")
        uploader.update_data_dict(
            data_dict,
            url_field="url",
            file_field="file",
            clear_field="clear",
        )
        if isinstance(uploader, Upload):
            # The default uploader will mangle our name so badly it removes
            # all randomness, which is actually impressive. This hack reverts
            # the munging that the default uploader does to restore randomness.
            uploader.filename = filename
            uploader.filepath = os.path.join(uploader.storage_path, filename)
            data_dict["url"] = filename

        uploader.upload()

        return {"filename": data_dict["url"]}
