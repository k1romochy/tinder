from fastapi import APIRouter


router = APIRouter(tags=['General'])


@router.get('/')
async def show_me():
    return {
        'message': 'Succefull'
    }