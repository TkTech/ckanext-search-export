import ckan.plugins as p
from ckan.plugins import toolkit
from flask import Blueprint

from ckanext.search_export.controller import search_export_create, search_export_status


class SearchExportPlugin(p.SingletonPlugin):
    """
    A plugin to export search results from CKAN.
    """

    p.implements(p.IConfigurer)
    p.implements(p.IBlueprint)

    @staticmethod
    def update_config(config):
        toolkit.add_template_directory(config, "templates")

    def get_blueprint(self):
        """
        Return a Flask Blueprint for the plugin's views.
        """
        blueprint = Blueprint("search_export", self.__module__)
        blueprint.add_url_rule(
            "/search_export",
            view_func=search_export_create,
            methods=["POST"],
            endpoint="search_export_create",
        )
        blueprint.add_url_rule(
            "/search_export/<string:job_id>",
            view_func=search_export_status,
            methods=["GET"],
            endpoint="search_export_status",
        )
        return blueprint
