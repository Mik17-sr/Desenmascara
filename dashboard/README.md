# Dashboard de Desenmascara

Las 4 vistas de la guía (sección 7): Radar en vivo (`/`), Verificar un mensaje con Rayos X (`/verificar`), Banco de números (`/banco`) y Panel de la entidad (`/entidad`).

```powershell
npm install
npm run build
npm run start      # http://localhost:3000
```

Necesita la API corriendo en `http://127.0.0.1:8000` (ver el README de la raíz). Para otra dirección: `NEXT_PUBLIC_API_URL=https://.../api/v1` antes de `npm run build`.

Solo lee vistas agregadas y anónimas. El Panel de la entidad pide la llave de acceso de la entidad; las revisiones y la lista blanca piden la llave del equipo (`ADMIN_API_KEY`).
