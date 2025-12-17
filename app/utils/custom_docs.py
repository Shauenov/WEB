from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.responses import HTMLResponse

def custom_swagger_ui_html(*, openapi_url: str, title: str = "Docs") -> HTMLResponse:
    html = get_swagger_ui_html(
        openapi_url=openapi_url,
        title=title,
        swagger_js_url="https://cdnjs.cloudflare.com/ajax/libs/swagger-ui/4.15.5/swagger-ui-bundle.js",
        swagger_css_url="https://cdnjs.cloudflare.com/ajax/libs/swagger-ui/4.15.5/swagger-ui.css",
    )

    custom_js = f"""
    <script>
    window.onload = function() {{
        const ui = SwaggerUIBundle({{
            url: '{openapi_url}',
            dom_id: '#swagger-ui',
            presets: [SwaggerUIBundle.presets.apis, SwaggerUIBundle.SwaggerUIStandalonePreset],
            layout: "BaseLayout"
        }});

        // взять токен из localStorage
        const token = localStorage.getItem("access_token");
        if (token) {{
            ui.preauthorizeApiKey("BearerAuth", token);
        }}

        // перехватить ответ sign-in
        const oldFetch = window.fetch;
        window.fetch = async (...args) => {{
            const response = await oldFetch(...args);
            if (args[0].includes("/auth/sign-in") && response.status === 200) {{
                const data = await response.clone().json();
                if (data.access_token) {{
                    localStorage.setItem("access_token", data.access_token);
                    ui.preauthorizeApiKey("BearerAuth", data.access_token);
                }}
            }}
            return response;
        }};
    }}
    </script>
    """

    return HTMLResponse(html.body.decode("utf-8") + custom_js)
