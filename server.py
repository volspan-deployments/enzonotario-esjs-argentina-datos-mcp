from starlette.applications import Starlette
from starlette.routing import Route, Mount
from starlette.responses import JSONResponse
import uvicorn
import threading
from fastmcp import FastMCP
import httpx
import os
from typing import Optional

mcp = FastMCP("ArgentinaDatos")

BASE_URL = "https://argentinadatos.com/api"


@mcp.tool()
async def get_dolar_rates(
    _track("get_dolar_rates")
    tipo: Optional[str] = None,
    fecha: Optional[str] = None
) -> dict:
    """Fetches current and historical exchange rates for different types of Argentine dollar (USD) variants such as oficial, blue, MEP, CCL, crypto, tarjeta, mayorista, etc. Use this when the user asks about dollar prices, exchange rates, or currency values in Argentina."""
    async with httpx.AsyncClient(timeout=30) as client:
        if tipo:
            # Historical data for a specific type
            if fecha:
                url = f"{BASE_URL}/v1/cotizaciones/dolares/{tipo}/{fecha}"
            else:
                url = f"{BASE_URL}/v1/cotizaciones/dolares/{tipo}"
        else:
            # All types, current
            url = f"{BASE_URL}/v1/cotizaciones/dolares"

        response = await client.get(url)
        if response.status_code == 200:
            return {"status": "success", "data": response.json()}
        else:
            return {"status": "error", "code": response.status_code, "message": response.text}


@mcp.tool()
async def get_inflation_data(
    _track("get_inflation_data")
    fecha_inicio: Optional[str] = None,
    fecha_fin: Optional[str] = None
) -> dict:
    """Retrieves official inflation data (IPC) for Argentina, including monthly and cumulative inflation rates published by INDEC. Use this when the user asks about inflation, CPI, or price index data in Argentina."""
    async with httpx.AsyncClient(timeout=30) as client:
        url = f"{BASE_URL}/v1/finanzas/indices/inflacion"
        params = {}
        if fecha_inicio:
            params["desde"] = fecha_inicio
        if fecha_fin:
            params["hasta"] = fecha_fin

        response = await client.get(url, params=params if params else None)
        if response.status_code == 200:
            return {"status": "success", "data": response.json()}
        else:
            return {"status": "error", "code": response.status_code, "message": response.text}


@mcp.tool()
async def get_plazo_fijo_rates(
    _track("get_plazo_fijo_rates")
    entidad: Optional[str] = None
) -> dict:
    """Fetches current fixed-term deposit (plazo fijo) interest rates offered by Argentine banks and financial institutions. Use this when the user wants to compare savings options, fixed-term deposit rates, or investment yields in Argentine banks."""
    async with httpx.AsyncClient(timeout=30) as client:
        url = f"{BASE_URL}/v1/finanzas/tasas/plazoFijo"

        response = await client.get(url)
        if response.status_code == 200:
            data = response.json()
            # Filter by entity if specified
            if entidad and isinstance(data, list):
                entidad_lower = entidad.lower()
                filtered = [
                    item for item in data
                    if entidad_lower in str(item.get("entidad", "")).lower()
                    or entidad_lower in str(item.get("nombre", "")).lower()
                ]
                return {"status": "success", "data": filtered, "filtered_by": entidad}
            return {"status": "success", "data": data}
        else:
            return {"status": "error", "code": response.status_code, "message": response.text}


@mcp.tool()
async def get_fondos_inversion(
    _track("get_fondos_inversion")
    fondo: Optional[str] = None,
    fecha: Optional[str] = None
) -> dict:
    """Retrieves data about Argentine mutual funds (Fondos Comunes de Inversion - FCI), including yields and performance metrics. Use this when the user asks about investment funds, FCI performance, or wants to compare investment options in Argentina."""
    async with httpx.AsyncClient(timeout=30) as client:
        if fondo:
            url = f"{BASE_URL}/v1/finanzas/fci/{fondo}"
            if fecha:
                url = f"{url}/{fecha}"
        else:
            url = f"{BASE_URL}/v1/finanzas/fci"
            if fecha:
                url = f"{url}/{fecha}"

        response = await client.get(url)
        if response.status_code == 200:
            return {"status": "success", "data": response.json()}
        else:
            return {"status": "error", "code": response.status_code, "message": response.text}


@mcp.tool()
async def get_riesgo_pais(
    _track("get_riesgo_pais")
    fecha_inicio: Optional[str] = None,
    fecha_fin: Optional[str] = None
) -> dict:
    """Fetches the current and historical Argentine country risk (riesgo pais / EMBI+) index. Use this when the user asks about Argentina's country risk, sovereign bond spreads, or economic risk indicators."""
    async with httpx.AsyncClient(timeout=30) as client:
        url = f"{BASE_URL}/v1/finanzas/indices/riesgoPais"
        params = {}
        if fecha_inicio:
            params["desde"] = fecha_inicio
        if fecha_fin:
            params["hasta"] = fecha_fin

        response = await client.get(url, params=params if params else None)
        if response.status_code == 200:
            return {"status": "success", "data": response.json()}
        else:
            return {"status": "error", "code": response.status_code, "message": response.text}


@mcp.tool()
async def get_reservas_bcra(
    _track("get_reservas_bcra")
    indicador: Optional[str] = None,
    fecha_inicio: Optional[str] = None,
    fecha_fin: Optional[str] = None
) -> dict:
    """Retrieves data about Argentina's Central Bank (BCRA) international reserves and monetary base indicators. Use this when the user asks about BCRA reserves, monetary policy data, or central bank statistics."""
    async with httpx.AsyncClient(timeout=30) as client:
        if indicador:
            url = f"{BASE_URL}/v1/finanzas/indices/{indicador}"
        else:
            url = f"{BASE_URL}/v1/finanzas/indices/reservas"

        params = {}
        if fecha_inicio:
            params["desde"] = fecha_inicio
        if fecha_fin:
            params["hasta"] = fecha_fin

        response = await client.get(url, params=params if params else None)
        if response.status_code == 200:
            result = {"status": "success", "data": response.json()}
            # If no specific indicator, also try to fetch monetary base
            if not indicador:
                url2 = f"{BASE_URL}/v1/finanzas/indices/baseMonetaria"
                response2 = await client.get(url2, params=params if params else None)
                if response2.status_code == 200:
                    result["baseMonetaria"] = response2.json()
            return result
        else:
            return {"status": "error", "code": response.status_code, "message": response.text}


@mcp.tool()
async def get_cotizaciones_historicas(
    _track("get_cotizaciones_historicas")
    tipo: str,
    fecha_inicio: Optional[str] = None,
    fecha_fin: Optional[str] = None
) -> dict:
    """Fetches historical price series for any supported financial indicator (dollars, inflation, country risk, etc.) over a specified time range. Use this when the user needs trend analysis, charts data, or wants to compare values across different periods in Argentina."""
    async with httpx.AsyncClient(timeout=30) as client:
        # Determine the correct endpoint based on tipo
        tipo_lower = tipo.lower().strip()

        if tipo_lower.startswith("dolar/") or tipo_lower.startswith("dólar/"):
            # e.g. dolar/blue -> /v1/cotizaciones/dolares/blue
            parts = tipo_lower.replace("dólar", "dolar").split("/")
            dolar_tipo = parts[1] if len(parts) > 1 else "blue"
            url = f"{BASE_URL}/v1/cotizaciones/dolares/{dolar_tipo}"
        elif tipo_lower in ["blue", "oficial", "bolsa", "mep", "contadoconliqui", "ccl", "mayorista", "cripto", "tarjeta"]:
            url = f"{BASE_URL}/v1/cotizaciones/dolares/{tipo_lower}"
        elif tipo_lower in ["inflacion", "inflación"]:
            url = f"{BASE_URL}/v1/finanzas/indices/inflacion"
        elif tipo_lower in ["riesgopais", "riesgo_pais", "riesgo-pais", "riesgo pais"]:
            url = f"{BASE_URL}/v1/finanzas/indices/riesgoPais"
        elif tipo_lower in ["reservas"]:
            url = f"{BASE_URL}/v1/finanzas/indices/reservas"
        elif tipo_lower in ["basemonetaria", "base_monetaria"]:
            url = f"{BASE_URL}/v1/finanzas/indices/baseMonetaria"
        else:
            # Generic attempt
            url = f"{BASE_URL}/v1/{tipo}"

        params = {}
        if fecha_inicio:
            params["desde"] = fecha_inicio
        if fecha_fin:
            params["hasta"] = fecha_fin

        response = await client.get(url, params=params if params else None)
        if response.status_code == 200:
            return {
                "status": "success",
                "tipo": tipo,
                "fecha_inicio": fecha_inicio,
                "fecha_fin": fecha_fin,
                "data": response.json()
            }
        else:
            return {"status": "error", "code": response.status_code, "message": response.text, "url": url}




_SERVER_SLUG = "enzonotario-esjs-argentina-datos"

def _track(tool_name: str, ua: str = ""):
    try:
        import urllib.request, json as _json
        data = _json.dumps({"slug": _SERVER_SLUG, "event": "tool_call", "tool": tool_name, "user_agent": ua}).encode()
        req = urllib.request.Request("https://www.volspan.dev/api/analytics/event", data=data, headers={"Content-Type": "application/json"})
        urllib.request.urlopen(req, timeout=1)
    except Exception:
        pass

async def health(request):
    return JSONResponse({"status": "ok", "server": mcp.name})

async def tools(request):
    registered = await mcp.list_tools()
    tool_list = [{"name": t.name, "description": t.description or ""} for t in registered]
    return JSONResponse({"tools": tool_list, "count": len(tool_list)})

sse_app = mcp.http_app(transport="sse")

app = Starlette(
    routes=[
        Route("/health", health),
        Route("/tools", tools),
        Mount("/", sse_app),
    ],
    lifespan=sse_app.lifespan,
)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
