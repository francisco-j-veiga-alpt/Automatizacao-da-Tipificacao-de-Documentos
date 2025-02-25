# temporary TODO: refactor

def sentiment_pipeline_filter_last_date_gte(date):
    return [
        {
            '$match': {
                'data': {'$gte': date}
            }
        },
        {
            '$project': {
                '_id': 0,
                'yearMonth': {
                    '$dateToString': {'format': '%Y-%m', 'date': '$data', 'timezone': 'UTC'}
                },
                'sentimento': 1,
            }
        },
        {
            '$facet': {
                'sentiment_by_month': [
                    {
                        '$group': {
                            '_id': {'yearMonth': '$yearMonth', 'sentimento': '$sentimento'},
                            'count': {'$sum': 1}
                        }
                    },
                    {
                        '$group': {
                            '_id': '$_id.yearMonth',
                            'sentiments': {
                                '$push': {'sentiment': '$_id.sentimento', 'count': '$count'}
                            }
                        }
                    },
                    {
                        '$project':{
                            '_id':0,
                            'yearMonth': '$_id',
                            'sentiments': 1
                        }
                    },
                    {
                        '$sort': {'yearMonth': -1, "count":-1}
                    }

                ],
                'total_sentiment': [
                    {
                        '$group': {
                            '_id': '$sentimento',
                            'count': {'$sum': 1}
                        }
                    },
                    {
                        '$project':{
                            '_id':0,
                            'sentiment':'$_id',
                            'count':1
                        }
                    },
                    {'$sort': {'count': -1}}
                ]
            }
        }

    ]

def total_negative_feedback_pipeline_filter_last_date_gte(date):
    return [
        {
            '$match': {
                'data': {'$gte': date},
                'sentimento': 'Negativo'
            }
        },
        {
            '$project': {
                '_id': 0,
                'yearMonth': {
                    '$dateToString': {'format': '%Y-%m', 'date': '$data', 'timezone': 'UTC'}
                },
            }
        },
        {
            '$facet': {
                'total_negative_count': [
                    {'$group': {'_id': None, 'count': {'$sum': 1}}},
                    {'$project': {'_id': 0, 'count': 1}}
                ],
                'negative_by_month': [
                    {
                        '$group': {
                            '_id': '$yearMonth',
                            'count': {'$sum': 1}
                        }
                    },
                    {
                        '$project': {
                            '_id': 0,
                            'yearMonth': '$_id',
                            'count': 1
                        }
                    },
                    {'$sort': {'yearMonth': 1}}
                ]
            }
        }
    ]

def total_negative_by_area_pipeline_filter_last_date_gte(date):
    return [
        {
            '$match': {
                'data': {'$gte': date},
                'sentimento': 'Negativo'
            }
        },
        {
            '$project': {
                '_id': 0,
                'yearMonth': {
                    '$dateToString': {'format': '%Y-%m', 'date': '$data', 'timezone': 'UTC'}
                },
                'area_de_feedback': 1
            }
        },
        {
            '$facet': {
                'total_negative_by_area': [
                    {
                        '$group': {
                            '_id': {
                                'area_de_feedback': '$area_de_feedback'
                            },
                            'count': {'$sum': 1}
                        }
                    },
                    {
                        '$project': {
                            '_id': 0,
                            'area_de_feedback': '$_id.area_de_feedback',
                            'count': 1
                        }
                    },
                    {'$sort': {'count': -1, 'area_de_feedback': 1}},
                    {'$limit': 10}
                ],
                'top10_negative_by_month_area': [
                    {
                        '$group': {
                            '_id': {
                                'yearMonth': '$yearMonth',
                                'area_de_feedback': '$area_de_feedback'
                            },
                            'count': {'$sum': 1}
                        }
                    },
                    {
                        '$sort': {
                            '_id.yearMonth': 1,
                            'count': -1
                            }
                    },
                    {
                        '$group': {
                            '_id': '$_id.yearMonth',
                            'top_entries': {'$push': {
                                'area_de_feedback': '$_id.area_de_feedback',
                                'count': '$count'
                                }
                            }
                        }
                    },
                    {
                        '$project':{
                            '_id': 0,
                            'yearMonth': '$_id',
                            'top_entries': { '$slice': ['$top_entries', 10]}
                        }
                    },
                        {'$sort': {'yearMonth': -1, 'count': -1, 'area_de_feedback': 1}}

                ]
            }
        }
    ]

def total_negative_by_area_class_pipeline_filter_last_date_gte(date):
    return [
        {
            '$match': {
                'data': {'$gte': date},
                'sentimento': 'Negativo'
            }
        },
        {
            '$project': {
                '_id': 0,
                'yearMonth': {
                    '$dateToString': {'format': '%Y-%m', 'date': '$data', 'timezone': 'UTC'}
                },
                'area_de_feedback': 1,
                'classificacao': 1
            }
        },
        {
            '$facet': {
                'total_negative_by_area_class': [
                    {
                        '$group': {
                            '_id': {
                                'area_de_feedback': '$area_de_feedback',
                                'classificacao': '$classificacao',
                            },
                            'count': {'$sum': 1}
                        }
                    },
                    {
                        '$project': {
                            '_id': 0,
                            'area_de_feedback': '$_id.area_de_feedback',
                            'classificacao': '$_id.classificacao',
                            'count': 1
                        }
                    },
                    {'$sort': {'count': -1, 'area_de_feedback': 1, 'classificacao': 1}},
                    {'$limit': 10}
                ],
                'top10_negative_by_month_area_class': [
                    {
                        '$group': {
                            '_id': {
                                'yearMonth': '$yearMonth',
                                'area_de_feedback': '$area_de_feedback',
                                'classificacao': '$classificacao',
                            },
                            'count': {'$sum': 1}
                        }
                    },
                    {
                        '$sort': {
                            '_id.yearMonth': 1,
                            'count': -1
                            }
                    },
                    {
                        '$group': {
                            '_id': '$_id.yearMonth',
                            'top_entries': {'$push': {
                                'area_de_feedback': '$_id.area_de_feedback',
                                'classificacao': '$_id.classificacao',
                                'count': '$count'
                                }
                            }
                        }
                    },
                    {
                        '$project':{
                            '_id': 0,
                            'yearMonth': '$_id',
                            'top_entries': { '$slice': ['$top_entries', 10]}
                        }
                    },
                        {'$sort': {'yearMonth': -1, 'count': -1, 'area_de_feedback': 1, 'classificacao': 1}}

                ]
            }
        }
    ]

def total_negative_by_area_class_topic_pipeline_filter_last_date_gte(date):
    return [
        {
            '$match': {
                'data': {'$gte': date},
                'sentimento': 'Negativo'
            }
        },
        {
            '$project': {
                '_id': 0,
                'yearMonth': {
                    '$dateToString': {'format': '%Y-%m', 'date': '$data', 'timezone': 'UTC'}
                },
                'area_de_feedback': 1,
                'classificacao': 1,
                'assunto': 1
            }
        },
        {
            '$facet': {
                'total_negative_by_area_class_topic': [
                    {
                        '$group': {
                            '_id': {
                                'area_de_feedback': '$area_de_feedback',
                                'classificacao': '$classificacao',
                                'assunto': '$assunto'
                            },
                            'count': {'$sum': 1}
                        }
                    },
                    {
                        '$project': {
                            '_id': 0,
                            'area_de_feedback': '$_id.area_de_feedback',
                            'classificacao': '$_id.classificacao',
                            'assunto': '$_id.assunto',
                            'count': 1
                        }
                    },
                    {'$sort': {'count': -1, 'area_de_feedback': 1, 'classificacao': 1, 'assunto': 1}},
                    {'$limit': 10}
                ],
                'top10_negative_by_month_area_class_topic': [
                    {
                        '$group': {
                            '_id': {
                                'yearMonth': '$yearMonth',
                                'area_de_feedback': '$area_de_feedback',
                                'classificacao': '$classificacao',
                                'assunto': '$assunto'
                            },
                            'count': {'$sum': 1}
                        }
                    },
                    {
                        '$sort': {
                            '_id.yearMonth': 1,
                            'count': -1
                            }
                    },
                    {
                        '$group': {
                            '_id': '$_id.yearMonth',
                            'top_entries': {'$push': {
                                'area_de_feedback': '$_id.area_de_feedback',
                                'classificacao': '$_id.classificacao',
                                'assunto': '$_id.assunto',
                                'count': '$count'
                                }
                            }
                        }
                    },
                    {
                        '$project':{
                            '_id': 0,
                            'yearMonth': '$_id',
                            'top_entries': { '$slice': ['$top_entries', 10]}
                        }
                    },
                        {'$sort': {'yearMonth': -1, 'count': -1, 'area_de_feedback': 1, 'classificacao': 1, 'assunto': 1}}

                ]
            }
        }
    ]

def total_urgente_pipeline_filter_last_date_gte(date):
    return [
        {
            '$match': {
                'data': {'$gte': date},
                'urgente': 'Sim'
            }
        },
        {
            '$project': {
                '_id': 0,
                'yearMonth': {
                    '$dateToString': {'format': '%Y-%m', 'date': '$data', 'timezone': 'UTC'}
                },
            }
        },
        {
            '$facet': {
                'total_urgent_count': [
                    {'$group': {'_id': None, 'count': {'$sum': 1}}},
                    {'$project': {'_id': 0, 'count': 1}}
                ],
                'urgent_by_month': [
                    {
                        '$group': {
                            '_id': '$yearMonth',
                            'count': {'$sum': 1}
                        }
                    },
                    {
                        '$project': {
                            '_id': 0,
                            'yearMonth': '$_id',
                            'count': 1
                        }
                    },
                    {'$sort': {'yearMonth': -1}}
                ]
            }
        }
    ]

