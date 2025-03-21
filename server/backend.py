from flask import request, send_from_directory, session
from retrieval.query import query_handler
from retrieval.query import QuerySet
from retrieval.adjust_query import add_item_to_query_set, remove_item_from_query_set
from server.results_to_html import results_to_html_dict
import os


class Backend_Api:
    def __init__(self, app, config: dict) -> None:
        self.app = app
        self.config = config
        self.index_dir_path = config['index_directory']
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
        # Get the input data from the AJAX request
        input_data = request.form['inputData']

        # Here you can call your Python function with input_data as the argument
        results, query_set = query_handler(self.index_dir_path, input_data)

        # update the global query set
        session['global_query_set'] = query_set.to_dict()
        entry_list = [result.to_app_dict() for result in results]
        entry_dict = {entry['case_id']: entry['max_entry'] for entry in entry_list}
        session['entry_dict'] = entry_dict

        results_dict = results_to_html_dict(results, query_set)
        return results_dict

    def _add_item(self):
        # Get the input data from the AJAX request
        input_data = request.form['case_id']
        add_id = str(input_data)
        query_set = session['global_query_set']
        entry_dict = session['entry_dict']
        query_set= QuerySet.from_dict(query_set)
        query_set = add_item_to_query_set(query_set, entry_dict, add_id)

        # rerun the query
        results, query_set = query_handler(self.index_dir_path, query_set)
        session['global_query_set'] = query_set.to_dict()
        entry_list = [result.to_app_dict() for result in results]
        entry_dict = {entry['case_id']: entry['max_entry'] for entry in entry_list}
        session['entry_dict'] = entry_dict
        results_dict = results_to_html_dict(results, query_set)
        return results_dict

    def _remove_item(self):
        # Get the input data from the AJAX request
        input_data = request.form['case_id']
        remove_id = str(input_data)
        query_set = session['global_query_set']
        query_set = QuerySet.from_dict(query_set)
        query_set = remove_item_from_query_set(query_set, remove_id)

        # rerun the query
        results, query_set = query_handler(self.index_dir_path, query_set)
        session['global_query_set'] = query_set.to_dict()
        entry_list = [result.to_app_dict() for result in results]
        entry_dict = {entry['case_id']: entry['max_entry'] for entry in entry_list}
        session['entry_dict'] = entry_dict
        results_dict = results_to_html_dict(results, query_set)
        return results_dict

    def _apply_weights(self):
        # Get the input data from the AJAX request
        input_data = request.form['weights']

        # Update the weights in the query set
        weights = [float(w) for w in input_data.split(",")]
        query_set = session['global_query_set']
        query_set= QuerySet.from_dict(query_set)
        query_set.weights = weights

        # rerun the query
        results, query_set = query_handler(self.index_dir_path, query_set)
        session['global_query_set'] = query_set.to_dict()
        entry_list = [result.to_app_dict() for result in results]
        entry_dict = {entry['case_id']: entry['max_entry'] for entry in entry_list}
        session['entry_dict'] = entry_dict
        results_dict = results_to_html_dict(results, query_set)
        return results_dict