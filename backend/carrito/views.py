from rest_framework import status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.core.mail import send_mail
from django.conf import settings
from .models import Carrito, ItemCarrito, Venta, DetalleVenta
from productos.models import Producto
from .serializers import CarritoSerializer, AgregarItemSerializer, VentaSerializer
from django.contrib.auth import get_user_model  

User = get_user_model()

class CarritoView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        carrito, _ = Carrito.objects.get_or_create(usuario=request.user)
        serializer = CarritoSerializer(carrito)
        return Response(serializer.data)

    def post(self, request):
        serializer = AgregarItemSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        producto = get_object_or_404(Producto, id=serializer.validated_data["producto_id"])
        cantidad = serializer.validated_data["cantidad"]

        if producto.stock < cantidad:
            return Response({"detail": "Stock insuficiente."}, status=400)

        carrito, _ = Carrito.objects.get_or_create(usuario=request.user)
        item, created = ItemCarrito.objects.get_or_create(carrito=carrito, producto=producto)
        item.cantidad = cantidad
        item.save()
        return Response({"detail": "Producto agregado o actualizado correctamente."}, status=200)

    def delete(self, request):
        producto_id = request.data.get("producto_id")
        carrito = get_object_or_404(Carrito, usuario=request.user)
        item = get_object_or_404(ItemCarrito, carrito=carrito, producto_id=producto_id)
        item.delete()
        return Response({"detail": "Producto eliminado del carrito."}, status=200)


class FinalizarCompraView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        metodo_pago = request.data.get("metodo_pago", "efectivo")
        carrito = get_object_or_404(Carrito, usuario=request.user)
        if not carrito.items.exists():
            return Response({"detail": "El carrito está vacío."}, status=400)

        total = sum(item.subtotal for item in carrito.items.all())

        venta = Venta.objects.create(usuario=request.user, total=total, metodo_pago=metodo_pago)
        for item in carrito.items.all():
            if item.producto.stock < item.cantidad:
                return Response({"detail": f"Stock insuficiente para {item.producto.nombre}"}, status=400)
            DetalleVenta.objects.create(
                venta=venta,
                producto=item.producto,
                cantidad=item.cantidad,
                precio_unitario=item.producto.precio
            )
            item.producto.stock -= item.cantidad
            item.producto.save()
        carrito.items.all().delete()

        detalles_lineas = []
        for d in venta.detalles.select_related("producto__categoria").all():
            detalles_lineas.append(
                f"- {d.producto.nombre} ({d.producto.categoria.nombre}) x{d.cantidad} = ${d.subtotal()}"
            )
        detalles_texto = "\n".join(detalles_lineas)

        cuerpo_cliente = (
            f"Hola {request.user.username}, gracias por tu compra.\n\n"
            f"Total: ${total}\n"
            f"Método de pago: {metodo_pago}\n\n"
            "Detalles:\n"
            f"{detalles_texto}"
        )

        send_mail(
            subject="Factura de tu compra",
            message=cuerpo_cliente,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[request.user.email],
            fail_silently=False,
        )

        superusers = User.objects.filter(is_superuser=True).values_list("email", flat=True)
        admin_emails = [e for e in superusers if e]

        if not admin_emails:
            fallback_admin = getattr(settings, "ADMIN_EMAIL", None) or settings.EMAIL_HOST_USER
            admin_emails = [fallback_admin]

        cuerpo_admin = (
            "Nueva venta realizada:\n\n"
            f"Cliente: {request.user.email}\n"
            f"Total: ${total}\n"
            f"Método de pago: {metodo_pago}\n\n"
            "Detalles:\n"
            f"{detalles_texto}"
        )

        send_mail(
            subject="Nueva venta en tu tienda",
            message=cuerpo_admin,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=admin_emails,
            fail_silently=False,
        )

        lineas_stock = []
        for producto in Producto.objects.select_related("categoria").all():
            if producto.stock == 0:
                estado = "AGOTADO"
            elif producto.stock <= 2:
                estado = "CASI AGOTADO"
            else:
                estado = "OK"

            lineas_stock.append(
                f"- {producto.nombre} ({producto.categoria.nombre}): "
                f"stock {producto.stock} -> {estado}"
            )

        cuerpo_stock = (
            "📦 Estado actual del catálogo de productos después de la última venta:\n\n"
            + "\n".join(lineas_stock)
        )

        send_mail(
            subject="📦 Estado actual del catálogo tras la última venta",
            message=cuerpo_stock,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[settings.ADMIN_EMAIL],
            fail_silently=False,
        )

        return Response(
            {
                "detail": "Compra finalizada. Factura enviada al correo.",
                "venta": VentaSerializer(venta).data,
            },
            status=200,
        )