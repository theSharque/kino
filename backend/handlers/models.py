"""
Models handlers (controllers)
"""
from aiohttp import web
from services.model_service import ModelService


async def get_model_categories(request: web.Request) -> web.Response:
    """
    Get all available model categories

    GET /api/v1/models/categories
    """
    try:
        categories = ModelService.get_model_categories()

        return web.json_response({
            'total': len(categories),
            'categories': categories
        }, status=200)

    except Exception as e:
        return web.json_response({
            'error': 'Internal server error',
            'message': str(e)
        }, status=500)


async def get_models_by_category(request: web.Request) -> web.Response:
    """
    Get all models in a specific category

    GET /api/v1/models/{category}
    """
    try:
        category = request.match_info['category']

        models = ModelService.get_models_by_category(category)

        return web.json_response({
            'category': category,
            'total': len(models),
            'models': models
        }, status=200)

    except Exception as e:
        return web.json_response({
            'error': 'Internal server error',
            'message': str(e)
        }, status=500)


async def get_model_info(request: web.Request) -> web.Response:
    """
    Get information about a specific model

    GET /api/v1/models/{category}/{filename}
    """
    try:
        category = request.match_info['category']
        filename = request.match_info['filename']

        model_info = ModelService.get_model_info(category, filename)

        if not model_info:
            return web.json_response({
                'error': 'Not found',
                'message': f'Model {filename} not found in category {category}'
            }, status=404)

        return web.json_response(model_info, status=200)

    except Exception as e:
        return web.json_response({
            'error': 'Internal server error',
            'message': str(e)
        }, status=500)

