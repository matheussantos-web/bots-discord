from datetime import datetime, timezone
from config import MONGO_URI, colecao_checkin


def _usando_mongo():
    return MONGO_URI is not None and colecao_checkin is not None


async def registrar_checkin(user_id_str, conteudo, call_id):
    if not _usando_mongo():
        return
    doc = await colecao_checkin.find_one({"_id": user_id_str})
    checkins = doc.get("checkins", []) if doc else []
    checkins.append({
        "conteudo": conteudo,
        "call_id": call_id,
        "entrou_em": datetime.now(timezone.utc).replace(tzinfo=None),
        "saiu_em": None,
        "minutos": 0,
    })
    await colecao_checkin.update_one(
        {"_id": user_id_str},
        {"$set": {"checkins": checkins}},
        upsert=True
    )


async def finalizar_checkin(user_id_str, call_id):
    if not _usando_mongo():
        return
    doc = await colecao_checkin.find_one({"_id": user_id_str})
    if not doc:
        return
    for ci in doc.get("checkins", []):
        if ci["call_id"] == call_id and ci["saiu_em"] is None:
            ci["saiu_em"] = datetime.now(timezone.utc).replace(tzinfo=None)
            entrada = ci["entrou_em"]
            if isinstance(entrada, datetime):
                if entrada.tzinfo is None:
                    entrada = entrada.replace(tzinfo=timezone.utc)
                ci["minutos"] = int((datetime.now(timezone.utc) - entrada).total_seconds() / 60)
            break
    await colecao_checkin.update_one({"_id": user_id_str}, {"$set": doc}, upsert=True)


async def obter_checkins(call_id):
    if not _usando_mongo():
        return []
    resultados = []
    async for doc in colecao_checkin.find({}):
        for ci in doc.get("checkins", []):
            if ci["call_id"] == call_id:
                resultados.append({"user_id": doc["_id"], **ci})
    return resultados
