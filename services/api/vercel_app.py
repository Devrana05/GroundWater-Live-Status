from main import app

# Vercel handler
def handler(request):
    return app(request.environ, lambda status, headers: None)