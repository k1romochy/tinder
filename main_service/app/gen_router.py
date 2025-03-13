from fastapi import APIRouter


router = APIRouter(tags=['General'])


@router.get('/')
async def AAAAAAAAAAAA_me():
    return {
        'message': 'Succefull'
    }