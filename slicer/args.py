import argparse

# Can we just integrate this properly?
try:
    from cubes_modeler import ModelEditorSlicerCommand
except ImportError:
    ModelEditorSlicerCommand = None

import slicer.commands as commands

################################################################################
# Main code

parser = argparse.ArgumentParser(description='Cubes tool')

subparsers = parser.add_subparsers(title='commands')
parser.add_argument('--cubes-debug',
                    dest='cubes_debug', action='store_true', default=False,
                            help='internal cubes debugging')
parser.set_defaults(func=lambda args:parser.print_help())

################################################################################
# Command: valdate_model

model_parser = subparsers.add_parser('model', help="logical model validation, translation, conversion")
model_subparsers = model_parser.add_subparsers(title='model commands',
                            help='additional model help')

parser_validate = model_subparsers.add_parser('validate',
                            help="validate model and print validation report")

parser_validate.add_argument('-d', '--defaults',
                            dest='show_defaults', action='store_true', default=False,
                            help='show defaults')
parser_validate.add_argument('--no-warnings',
                            dest='show_warnings', action='store_false', default=True,
                            help='disable warnings')

parser_validate.add_argument('model', help='model reference - can be a local file path or URL')
parser_validate.set_defaults(func=commands.validate_model)


################################################################################
# Command: edit

if ModelEditorSlicerCommand:
    subparser = model_subparsers.add_parser("edit", help="edit model")

    command = ModelEditorSlicerCommand()
    command.configure_parser(subparser)
    subparser.set_defaults(func=command)


################################################################################
# Command: convert

subparser = model_subparsers.add_parser('convert')
subparser.add_argument('--format',
                            dest='format',
                            choices=('json', 'bundle'),
                            default='json',
                            help='output model format')
subparser.add_argument('--force',
                            dest='force', action='store_true', default=False,
                            help='replace existing model bundle')
subparser.add_argument('model', help='model reference - can be a path or URL')
subparser.add_argument('target', help='target output path', nargs='?', default=None)
subparser.set_defaults(func=commands.convert_model)


################################################################################
# Command: serve

subparser = subparsers.add_parser('serve', help="run slicer server")
subparser.add_argument('config', help='server confuguration .ini file')
subparser.set_defaults(func=commands.run_server)
subparser.set_defaults(foo="BAR")

subparser.add_argument('--debug',
                            dest='debug', action='store_true', default=False,
                            help="Run the server in debug mode")

subparser.add_argument('--visualizer',
                            dest='visualizer',
                            help="Visualizer URL or "
                                 "'default' for built-in visualizer")

################################################################################
# Command: serve

subparser = subparsers.add_parser('test', help="test the configuration and model with backend")
subparser.add_argument('config', help='server confuguration .ini file')
subparser.add_argument('cube', help='cube to test', nargs='*', default=[])
subparser.set_defaults(func=commands.run_test)

subparser.add_argument('--aggregate',
                            dest='aggregate', action='store_true', default=False,
                            help="Test aggregate of whole cube")

subparser.add_argument('-E', '--exclude-store',
                            dest='exclude_stores', action='append')

subparser.add_argument('--store',
                            dest='include_stores', action='append')

################################################################################
# Command: denormalize

subparser = subparsers.add_parser('denormalize',
                                  help="create denormalized view(s) using SQL star backend")
subparser.add_argument('config', help='slicer confuguration .ini file')
subparser.add_argument('-p', '--prefix',
                            dest='prefix',
                            help='prefix for denormalized views (overrides config value)')
subparser.add_argument('-f', '--force',
                            dest='replace', action='store_true', default=False,
                            help='replace existing views')
subparser.add_argument('-m', '--materialize',
                            dest='materialize', action='store_true', default=False,
                            help='create materialized view (table)')
subparser.add_argument('-i', '--index',
                            dest='index', action='store_true', default=False,
                            help='create index for key attributes')
subparser.add_argument('-s', '--schema',
                            dest='schema',
                            help='target view schema (overrides config value)')
subparser.add_argument('-c', '--cube',
                            dest='cube', action='append',
                            help='cube(s) to be denormalized, if not specified then all in the model')
subparser.set_defaults(func=commands.denormalize)

################################################################################
# Command: ddl

subparser = subparsers.add_parser('ddl', help="generate DDL of star schema, based on logical model (works only for SQL backend)")
subparser.add_argument('url', help='SQL database connection URL')
subparser.add_argument('model', help='model reference - can be a local file path or URL')
subparser.add_argument('--dimension-prefix',
                            dest='dimension_prefix',
                            help='prefix for dimension tables')
subparser.add_argument('--fact-prefix',
                            dest='fact_prefix',
                            default="",
                            help='prefix for fact tables')
subparser.add_argument('--dimension-suffix',
                       dest='dimension_suffix',
                       help='suffix for dimension tables')
subparser.add_argument('--fact-suffix',
                       dest='fact_suffix',
                       default="",
                       help='suffix for fact tables')
subparser.add_argument('--backend',
                            dest='backend',
                            help='backend name (currently limited only to SQL backends)')
subparser.set_defaults(func=commands.generate_ddl)
