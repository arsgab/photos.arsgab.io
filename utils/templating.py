from jinja2.filters import do_mark_safe

from markup import renderer_ref


def render_template(template_name: str, ctx: dict = None) -> str:
    renderer = renderer_ref.get()
    if not template_name.endswith('.html'):
        template_name = f'{template_name}.html'
    ctx = ctx or {}
    template = renderer.get_template(template_name)
    rendered = template.render(ctx)
    return do_mark_safe(rendered)


def render_template_partial(partial_name: str, ctx: dict = None) -> str:
    return render_template(f'partials/{partial_name}', ctx=ctx)
