from flask import render_template
from flask import make_response
from flask import url_for
from flask import Blueprint
from jinja2 import Markup
import re
import json

JSGLUE_JS_PATH = '/jsglue.js'
JSGLUE_NAMESPACE = 'Flask'
rule_parser = re.compile(r'<(.+?)>')
splitter = re.compile(r'<.+?>')

bp = Blueprint('jsglue', __name__, template_folder='templates')


def get_routes(app):
    output = []
    for r in app.url_map.iter_rules():
        endpoint = r.endpoint
        rule = '{root}{rule}'.format(root=app.config['APPLICATION_ROOT'], rule=r.rule) if app.config[
            'APPLICATION_ROOT'] else r.rule
        rule_args = [x.split(':')[-1] for x in rule_parser.findall(rule)]
        rule_tr = splitter.split(rule)
        output.append((endpoint, rule_tr, rule_args))
    return sorted(output, key=lambda x: len(x[1]), reverse=True)


class JSGlue(object):
    def __init__(self, app=None, url_prefix="", **kwargs):
        self.app = app
        self.url_prefix = url_prefix
        if app is not None:
            self.init_app(app, url_prefix)

    def init_app(self, app, url_prefix=""):
        self.app = app
        self.url_prefix = url_prefix

        app.register_blueprint(bp)

        @app.route(url_prefix + JSGLUE_JS_PATH)
        def serve_js():
            return make_response(
                (self.generate_js(), 200, {'Content-Type': 'text/javascript'})
            )

        @app.context_processor
        def context_processor():
            return {'JSGlue': JSGlue}

    def generate_js(self):
        rules = get_routes(self.app)
        # .js files are not autoescaped in flask
        return render_template(
            'jsglue/js_bridge.js',
            namespace=JSGLUE_NAMESPACE,
            rules=json.dumps(rules))

    @staticmethod
    def include():
        js_path = url_for('serve_js')
        return Markup('<script src="%s" type="text/javascript"></script>') % (js_path,)
