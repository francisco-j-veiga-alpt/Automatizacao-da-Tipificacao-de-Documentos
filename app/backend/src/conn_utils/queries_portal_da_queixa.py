
def results_total_by_month_filter_last_date_gte(date):
    return [
            {
                "$match": {
                    'data': {'$gte': date},
                }
            },
            {
                "$group": {
                    "_id": {
                        "year": {"$year": "$data"},
                        "month": {"$month": "$data"},
                        "sentiment": "$sentimento",
                        "area": "$area_de_feedback",
                        "classificacao": "$classificacao",
                        "assunto": "$assunto",
                    },
                    "count": {"$sum": 1},
                }
            },
            {
                "$sort": {"count": -1},  # Sort assuntos by count
            },
            {
                "$group": {
                    "_id": {
                        "year": "$_id.year",
                        "month": "$_id.month",
                        "sentiment": "$_id.sentiment",
                        "area": "$_id.area",
                        "classificacao": "$_id.classificacao",
                    },
                    "assuntos": {
                        "$push": {
                            "assunto": "$_id.assunto",
                            "count": "$count",
                        }
                    },
                    "count": {"$sum": "$count"},
                }
            },
            {
                "$sort": {"count": -1},  # Sort classificacoes by count
            },
            {
                "$group": {
                    "_id": {
                        "year": "$_id.year",
                        "month": "$_id.month",
                        "sentiment": "$_id.sentiment",
                        "area": "$_id.area",
                    },
                    "classificacoes": {
                        "$push": {
                            "classificacao": "$_id.classificacao",
                            "count": "$count",
                            "assuntos": "$assuntos",
                        }
                    },
                    "count": {"$sum": "$count"},
                }
            },
            {
                "$sort": {"count": -1},  # Sort areas by count
            },
            {
                "$group": {
                    "_id": {
                        "year": "$_id.year",
                        "month": "$_id.month",
                        "sentiment": "$_id.sentiment",
                    },
                    "areas": {
                        "$push": {
                            "area": "$_id.area",
                            "count": "$count",
                            "classificacoes": "$classificacoes",
                        }
                    },
                    "count": {"$sum": "$count"},
                }
            },
            {
                    "$sort": {"count": -1},  # Sort sentiments by count
            },
            {
                "$group": {
                    "_id": {
                        "year": "$_id.year",
                        "month": "$_id.month",
                    },
                    "sentiments": {
                        "$push": {
                            "sentiment": "$_id.sentiment",
                            "count": "$count",
                            "areas": "$areas",
                        }
                    },
                }
            },
            {
                "$project": {
                    "_id": 0,
                    "yearMonth": {
                        "$concat": [
                            {"$toString": "$_id.year"},
                            "/",
                            {"$toString": "$_id.month"},
                        ]
                    },
                    "sentiments": 1,
                }
            },
            {
                "$sort": {"yearMonth": 1} #sort in descendent order
            },
            {
                "$group": {
                    "_id": None,
                    "results_total_by_mont": {"$push": "$$ROOT"}
                }
            },
            {
                "$project": {
                    "_id": 0,
                    "results_total_by_mont": 1
                }
            }
        ]