from fastapi import APIRouter
router = APIRouter(prefix='/api/c2pa', tags=['c2pa'])
@router.get('/status')
def status():
    return {'status': 'ready', 'message': 'C2PA detection runs through the tool registry using the configured c2patool runtime.'}
