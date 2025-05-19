from flask import request, send_from_directory
from retrieval.query import query_handler
from retrieval.query import QuerySet
from retrieval.adjust_query import add_item_to_query_set, remove_item_from_query_set
from server.results_to_html import results_to_html_dict
import secrets
import os
from server.database import NaiveDatabase


class Backend_Api:
    def __init__(self, app, config: dict) -> None:
        self.app = app
        self.config = config
        self.index_dir_path = config['index_directory']
        self.database = NaiveDatabase(max_size=100)
        self.routes = {
            '/backend-api/query': {
                'function': self._query,
                'methods': ['POST']
            },
            '/backend-api/add_item': {
                'function': self._add_item,
                'methods': ['POST']
            },
            '/backend-api/remove_item': {
                'function': self._remove_item,
                'methods': ['POST']
            },
            '/backend-api/apply-weights': {
                'function': self._apply_weights,
                'methods': ['POST']
            },
            '/backend-api/img/<path:subpath>': {
                'function': self._load_img,
                'methods': ['GET']
            },
            '/temp/<path:subpath>': {
                'function': self._load_temp_img,
                'methods': ['GET']
            }
        }

    def _get_session_id(self):
        session_id = request.cookies.get("_archseek_server_session")
        if not session_id:
            session_id = secrets.token_hex(16)
        return session_id

    def _load_img(self, subpath):
        try:
            later_path = os.path.normpath(subpath)
            prefix_path = os.path.abspath('data')
            full_path = os.path.join(prefix_path, later_path)
            directory = os.path.dirname(full_path)
            filename = os.path.basename(full_path)
            return send_from_directory(directory, filename)
        except Exception as e:
            return {
                'success': False,
                "error": f"an error occurred {str(e)}"}, 400
        
    def _load_temp_img(self, subpath):
        try:
            later_path = os.path.normpath(subpath)
            prefix_path = os.path.abspath('temp')
            full_path = os.path.join(prefix_path, later_path)
            directory = os.path.dirname(full_path)
            filename = os.path.basename(full_path)
            return send_from_directory(directory, filename)
        except Exception as e:
            return {
                'success': False,
                "error": f"an error occurred {str(e)}"}, 400
        
    def _query(self):
        user_id = self._get_session_id()

        # Get the input data from the AJAX request
        input_data = request.form['inputData']

        # Here you can call your Python function with input_data as the argument
        results, query_set = query_handler(self.index_dir_path, input_data)

        # update the global query set
        self.database.update_or_insert(user_id, 'global_query_set', query_set.to_dict())
        entry_list = [result.to_app_dict() for result in results]
        entry_dict = {entry['case_id']: entry['max_entry'] for entry in entry_list}
        self.database.update_or_insert(user_id, 'entry_dict', entry_dict)

        results_dict = results_to_html_dict(results, query_set)
        return results_dict

    def _add_item(self):
        user_id = self._get_session_id()
        # Get the input data from the AJAX request
        input_data = request.form['case_id']
        add_id = str(input_data)
        query_set = self.database.get(user_id, 'global_query_set')
        entry_dict = self.database.get(user_id, 'entry_dict')
        query_set= QuerySet.from_dict(query_set)
        query_set = add_item_to_query_set(query_set, entry_dict, add_id)

        # rerun the query
        results, query_set = query_handler(self.index_dir_path, query_set)
        self.database.update_or_insert(user_id, 'global_query_set', query_set.to_dict())
        entry_list = [result.to_app_dict() for result in results]
        entry_dict = {entry['case_id']: entry['max_entry'] for entry in entry_list}
        self.database.update_or_insert(user_id, 'entry_dict', entry_dict)
        results_dict = results_to_html_dict(results, query_set)
        return results_dict

    def _remove_item(self):
        user_id = self._get_session_id()
        # Get the input data from the AJAX request
        input_data = request.form['case_id']
        remove_id = str(input_data)
        query_set = self.database.get(user_id, 'global_query_set')
        query_set = QuerySet.from_dict(query_set)
        query_set = remove_item_from_query_set(query_set, remove_id)

        # rerun the query
        results, query_set = query_handler(self.index_dir_path, query_set)
        self.database.update_or_insert(user_id, 'global_query_set', query_set.to_dict())
        entry_list = [result.to_app_dict() for result in results]
        entry_dict = {entry['case_id']: entry['max_entry'] for entry in entry_list}
        self.database.update_or_insert(user_id, 'entry_dict', entry_dict)
        results_dict = results_to_html_dict(results, query_set)
        return results_dict

    def _apply_weights(self):
        user_id = self._get_session_id()
        # Get the input data from the AJAX request
        input_data = request.form['weights']

        # Update the weights in the query set
        weights = [float(w) for w in input_data.split(",")]
        query_set = self.database.get(user_id, 'global_query_set')
        query_set= QuerySet.from_dict(query_set)
        query_set.weights = weights

        # rerun the query
        results, query_set = query_handler(self.index_dir_path, query_set)
        self.database.update_or_insert(user_id, 'global_query_set', query_set.to_dict())
        entry_list = [result.to_app_dict() for result in results]
        entry_dict = {entry['case_id']: entry['max_entry'] for entry in entry_list}
        self.database.update_or_insert(user_id, 'entry_dict', entry_dict)
        results_dict = results_to_html_dict(results, query_set)
        return results_dict