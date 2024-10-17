from django.shortcuts import render


def render_module_plugin(request, obj):
    return render(
        request,
        "djangocms_modules/render_module.html",
        {
            "object": obj,
        },
    )
