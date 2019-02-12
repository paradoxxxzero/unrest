try:
    import yaml
except ImportError:
    yaml = None

from ..util import Response


class YamlIdiom(object):
    def __init__(self, rest):
        self.rest = rest
        if yaml is None:
            raise ImportError(
                'You must have pyyaml installed to use this idiom'
            )

    def request_to_data(self, request):
        # if request.headers['Content-Type'] != 'application/yaml':
        #     return
        if request.payload:
            try:
                return yaml.load(request.payload.decode('utf-8'))
            except yaml.JSONDecodeError as e:
                self.rest.raise_error(400, 'YAML Error in payload: %s' % e)

    def data_to_response(self, data, method, status=200):
        if (
            method == 'GET'
            and self.rest.unrest.empty_get_as_404
            and 'occurences' in data
            and data['occurences'] == 0
        ):
            status = 404
        payload = yaml.dump(data, default_flow_style=False)
        headers = {'Content-Type': 'text/yaml'}
        response = Response(payload, headers, status)
        return response
