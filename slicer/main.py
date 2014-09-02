# -*- encoding: utf-8 -*-

"""Slicer tool

    For more information run: slicer --help

    Author: Stefan Urbanek <stefan.urbanek@gmail.com>
    Date: 2011-01
"""

from __future__ import absolute_import
from __future__ import print_function

from cubes import compat

import json
import sys
import cubes
import os

from collections import OrderedDict

from cubes.common import MissingPackageError
from cubes.logging import create_logger
from cubes.errors import CubesError
from cubes.metadata import read_model_metadata, write_model_metadata_bundle
from cubes import server

try:
    from cubes_modeler import ModelEditorSlicerCommand
except ImportError:
    ModelEditorSlicerCommand = None

def validate_model(args):
    """docstring for validate_model"""
    print("Reading model %s" % args.model)
    model = cubes.read_model_metadata(args.model)

    print("Validating model...\n")
    result = cubes.providers.validate_model(model)

    error_count = 0
    warning_count = 0
    default_count = 0

    for error in result:
        if error.scope == "model":
            scope = "model"
        else:
            if error.object:
                scope = "%s '%s'" % (error.scope, error.object)
            else:
                scope = "unknown %s" % error.scope

        if error.property:
            scope += " property '%s'" % error.property

        show = True
        if error.severity == "error":
            error_count += 1
        elif error.severity == "warning":
            warning_count += 1
            show = args.show_warnings
        elif error.severity == "default":
            show = args.show_defaults
            default_count += 1

        if show:
            print("%s in %s: %s"
                  % (error.severity.upper(), scope, error.message))

    if error_count == 0:
        if warning_count == 0:
            if default_count == 0:
                verdict = "model can be used"
            else:
                verdict = "model can be used, " \
                          "make sure that the defaults reflect reality"
        else:
            verdict = "not recommended to use the model, " \
                      "some issues might emerge"
    else:
        verdict = "model can not be used"

    print("")
    print("Defaults used  %d" % default_count)
    print("Warning        %d" % warning_count)
    print("Errors         %d" % error_count)
    print("Summary        %s" % verdict)

    if error_count > 0:
        exit(1)

def convert_model(args):
    raise NotImplementedError("Temporarily disabled.")

    path = args.target

    workspace = cubes.Workspace()
    for model in args.models:
        workspace.import_model(model)

    if args.format == "bundle":
        if os.path.exists(path):
            if not os.path.isdir(path):
                raise CubesError("Target exists and is a file, "
                                 "can not replace")
            elif not os.path.exists(os.path.join(path, "model.json")):
                raise CubesError("Target is not a model directory, "
                                    "can not replace.")
            if args.force:
                shutil.rmtree(path)
            else:
                raise CubesError("Target already exists. "
                                    "Remove it or use --force.")
        cubes.write_model_bundle(model, args.target)

    elif args.format == "json":
        info = model.to_dict(target="origin")
        if not path:
            print(json.dumps(info))
        else:
            with open(path, "w") as f:
                json.dump(info, f)

def model_to_json(args):
    raise NotImplementedError("Temporarily disabled.")

def update_locale(args):
    raise NotImplementedError("update of localizable dictionary is not yet implemented")

def extract_locale(args):
    raise NotImplementedError("Temporarily disabled.")
    model = cubes.model_from_path(args.model)
    print(json.dumps(model.localizable_dictionary()))

def translate_model(args):
    raise NotImplementedError("Temporarily disabled.")
    model = cubes.model_from_path(args.model)
    trans_path = args.translation

    with open(trans_path) as f:
        trans_dict = json.load(f)

    model = model.localize(trans_dict)
    dump_model(model)

def dump_model(model):
    print(json.dumps(model.to_dict(with_mappings=True)))

def read_config(cfg):
    """Read the configuration file."""
    config = compat.ConfigParser()
    try:
        config.read(args.config)
    except Exception as e:
        raise Exception("Unable to load config: %s" % e)

    return config

def generate_ddl(args):
    raise NotImplementedError("Temporarily disabled.")
    model = cubes.load_model(args.model)

    if args.backend:
        backend = cubes.workspace.get_backend(args.backend)
    else:
        backend = cubes.backends.sql.browser

    ddl = backend.ddl_for_model(args.url, model, fact_prefix=args.fact_prefix,
                                dimension_prefix=args.dimension_prefix,
                                fact_suffix=args.fact_suffix,
                                dimension_suffix=args.dimension_suffix)

    print(ddl)


def run_server(args):
    """Run Slicer HTTP server."""
    config = read_config(args.config)

    if config.has_option("server", "pid_file"):
        path = config.get("server", "pid_file")
        try:
            with open(path, "w") as f:
                f.write("%s\n" % os.getpid())
        except IOError:
            raise CubesError("Unable to write PID file '%s'. Check the "
                             "directory existence or permissions." % path)

    if args.visualizer:
        config.set("server", "visualizer", args.visualizer)

    cubes.server.run_server(config, debug=args.debug)


def run_test(args):
    """Test every cube in the model."""
    workspace = cubes.Workspace(args.config)

    errors = []

    if args.cube:
        cube_list = args.cube
    else:
        cube_list = [c["name"] for c in workspace.list_cubes()]

    exclude = args.exclude_stores or []
    include = args.include_stores or []

    tested = 0

    for name in cube_list:
        cube = workspace.cube(name)

        sys.stdout.write("testing %s: " % name)

        if cube.datastore in exclude \
                or (include and cube.datastore not in include):
            sys.stdout.write("pass\n")
            continue

        try:
            browser = workspace.browser(name)
        except Exception as e:
            errors.append((name, e))
            sys.stdout.write("BROWSER ERROR\n")
            continue

        tested += 1

        try:
            facts = browser.test(aggregate=args.aggregate)
        except NotImplementedError:
            sys.stdout.write("pass - no test\n")
        except CubesError as e:
            errors.append((name, e))
            sys.stdout.write("ERROR\n")

    print("\ntested %d cubes" % tested)
    if errors:
        print("%d ERRORS:" % len(errors))
        for (cube, e) in errors:
            if hasattr(e, "error_type"):
                etype = e.error_type
            else:
                etype = str(type(e))

            print("%s: %s - %s" % (cube, etype, str(e)))
    else:
        print("test passed")


def convert_model(args):
    path = args.target
    model = read_model_metadata(args.model)

    if args.format == "json":
        if not path:
            print(json.dumps(model, indent=4))
        else:
            with open(path, "w") as f:
                json.dump(model, f, indent=4)
    elif args.format == "bundle":
        write_model_metadata_bundle(path, model, replace=args.force)


def denormalize(args):
    # raise NotImplementedError("Temporarily disabled.")
    cube_list = args.cube
    config = read_config(args.config)

    workspace = cubes.Workspace(config)

    if not cube_list:
        cube_list = [cube["name"] for cube in workspace.list_cubes()]

    view_schema = args.schema # or workspace.options.get("denormalized_view_schema")
    view_prefix = args.prefix or workspace.options.get("denormalized_view_prefix")

    for cube_name in cube_list:
        cube = workspace.cube(cube_name)
        store = workspace.get_store(cube.datastore or "default")

        view_name = view_prefix + cube_name if view_prefix else cube_name

        print("denormalizing cube '%s' into '%s'" % (cube_name, view_name))

        store.create_denormalized_view(cube, view_name,
                                            materialize=args.materialize,
                                            replace=args.replace,
                                            create_index=args.index,
                                            keys_only=False,
                                            schema=view_schema)

def convert_model(args):
    path = args.target
    model = read_model_metadata(args.model)

    if args.format == "json":
        if not path:
            print(json.dumps(model, indent=4))
        else:
            with open(path, "w") as f:
                json.dump(model, f, indent=4)
    elif args.format == "bundle":
        write_model_metadata_bundle(path, model, replace=args.force)


def edit_model(args):
    if not run_modeler:
        sys.stderr.write("ERROR: 'cubes_modeler' package needs to be "
                         "installed to edit the model.\n")
        exit(1)

    if args.port:
        port = int(args.port)
    else:
        port = 5000

    import webbrowser
    webbrowser.open("http://127.0.0.1:%s" % port)

    run_modeler(args.model, args.target)

def main():
    args = parser.parse_args(sys.argv[1:])

    if not args.func:
        parser.print_help()
        exit(0)

    if args.cubes_debug:
        args.func(args)
    else:
        try:
            args.func(args)
        except CubesError as e:
            sys.stderr.write("ERROR: %s\n" % e)
            exit(1)
        except MissingPackageError as e:
            sys.stderr.write("MISSING PACKAGE ERROR: %s\n" % e)
            exit(2)
