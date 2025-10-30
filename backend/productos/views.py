from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from .models import Categoria, Producto
from .serializers import CategoriaSerializer, ProductoSerializer
from usuarios.permissions import EsAdmin



@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated, EsAdmin])
def categorias_admin(request):
    if request.method == 'GET':
        categorias = Categoria.objects.all()
        serializer = CategoriaSerializer(categorias, many=True)
        return Response(serializer.data)

    elif request.method == 'POST':
        serializer = CategoriaSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['PUT', 'DELETE'])
@permission_classes([IsAuthenticated, EsAdmin])
def categoria_detalle(request, pk):
    try:
        categoria = Categoria.objects.get(pk=pk)
    except Categoria.DoesNotExist:
        return Response({'error': 'Categoría no encontrada'}, status=404)

    if request.method == 'PUT':
        serializer = CategoriaSerializer(categoria, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)

    elif request.method == 'DELETE':
        categoria.delete()
        return Response({'message': 'Categoría eliminada'}, status=204)



@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated, EsAdmin])
def productos_admin(request):
    if request.method == 'GET':
        productos = Producto.objects.all()
        serializer = ProductoSerializer(productos, many=True)
        return Response(serializer.data)

    elif request.method == 'POST':
        serializer = ProductoSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)


@api_view(['PUT', 'DELETE'])
@permission_classes([IsAuthenticated, EsAdmin])
def producto_detalle(request, pk):
    try:
        producto = Producto.objects.get(pk=pk)
    except Producto.DoesNotExist:
        return Response({'error': 'Producto no encontrado'}, status=404)

    if request.method == 'PUT':
        serializer = ProductoSerializer(producto, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)

    elif request.method == 'DELETE':
        producto.delete()
        return Response({'message': 'Producto eliminado'}, status=204)


# --- ENDPOINT PÚBLICO ---
@api_view(['GET'])
@permission_classes([AllowAny])
def productos_por_categoria(request, categoria_id):
    try:
        categoria = Categoria.objects.get(pk=categoria_id)
    except Categoria.DoesNotExist:
        return Response({'error': 'Categoría no encontrada'}, status=404)

    productos = Producto.objects.filter(categoria=categoria)
    serializer = ProductoSerializer(productos, many=True)
    return Response({
        'categoria': categoria.nombre,
        'productos': serializer.data
    })
