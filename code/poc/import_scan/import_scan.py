#!/usr/bin/env python3
import ast
import yaml
import click


class Analyzer(ast.NodeVisitor):
    def __init__(self):
        self.import_stmt_stats = []

    def visit_Import(self, node):
        for alias in node.names:
            self.import_stmt_stats.append({
                "pkg": None,
                "name": alias.name,
                "as": alias.asname
            })
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        for alias in node.names:
            self.import_stmt_stats.append({
                "pkg": node.module,
                "name": alias.name,
                "as": alias.asname
            })
        self.generic_visit(node)

    def report(self, y):
        def build_py_import_stmt(i):
            as_clause = " as {}".format(i['as']) if i['as'] else ""
            from_clause = "from {} ".format(i['pkg']) if i['pkg'] else ""
            import_stmt = "{}import {}{}".format(from_clause, i['name'], as_clause)
            return import_stmt

        if y:
            print(yaml.dump(self.import_stmt_stats))
        else:
            format_out = map(build_py_import_stmt, self.import_stmt_stats)
            for o in format_out:
                print(o)


@click.command()
@click.argument(
    'py_src', required=True, type=click.File('r')
)
@click.option(
    '-y', help="Output result in yaml", is_flag=True
)
def main(py_src, y):
    """Given python source, scan all the 'import' statements from AST"""
    tree = ast.parse(py_src.read())

    analyzer = Analyzer()
    analyzer.visit(tree)
    analyzer.report(y)


if __name__ == "__main__":
    main()

