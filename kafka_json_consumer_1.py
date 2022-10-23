import argparse

from confluent_kafka import Consumer
from confluent_kafka.serialization import SerializationContext, MessageField
from confluent_kafka.schema_registry import SchemaRegistryClient
from confluent_kafka.schema_registry.json_schema import JSONDeserializer
import pandas as pd
from csv import DictWriter
import json


keys_file = open("/Users/abhisheksharma/Desktop/Kafka/API_keys/cloud_api_keys.txt","r+")
keys = keys_file.readlines()

API_KEY = keys[0].strip()
ENDPOINT_SCHEMA_URL  = 'https://psrc-8kz20.us-east-2.aws.confluent.cloud'
API_SECRET_KEY = keys[1].strip()
BOOTSTRAP_SERVER = keys[2].strip()
SECURITY_PROTOCOL = 'SASL_SSL'
SSL_MACHENISM = 'PLAIN'
SCHEMA_REGISTRY_API_KEY = keys[3].strip()
SCHEMA_REGISTRY_API_SECRET = keys[4].strip()


def sasl_conf():

    sasl_conf = {'sasl.mechanism': SSL_MACHENISM,
                 # Set to SASL_SSL to enable TLS support.
                #  'security.protocol': 'SASL_PLAINTEXT'}
                'bootstrap.servers':BOOTSTRAP_SERVER,
                'security.protocol': SECURITY_PROTOCOL,
                'sasl.username': API_KEY,
                'sasl.password': API_SECRET_KEY
                }
    return sasl_conf



def schema_config():
    return {'url':ENDPOINT_SCHEMA_URL,
    
    'basic.auth.user.info':f"{SCHEMA_REGISTRY_API_KEY}:{SCHEMA_REGISTRY_API_SECRET}"

    }


class Restaurant:   
    def __init__(self,record:dict):
        for k,v in record.items():
            setattr(self,k,v)
        
        self.record=record
   
    @staticmethod
    def dict_to_restaurant(data:dict,ctx):
        return Restaurant(record=data)

    def __str__(self):
        return f"{self.record}"


def main(topic):

    schema_registry_conf = schema_config()
    schema_registry_client = SchemaRegistryClient(schema_registry_conf)
    my_schema = schema_registry_client.get_schema(100003)
    schema_str = my_schema.schema_str
    json_deserializer = JSONDeserializer(schema_str,
                                         from_dict=Restaurant.dict_to_restaurant)

    consumer_conf = sasl_conf()
    consumer_conf.update({
                     'group.id': 'group1',
                     'auto.offset.reset': "earliest"})

    consumer = Consumer(consumer_conf)
    consumer.subscribe([topic])

    
    while True:
        try:
            # SIGINT can't be handled when polling, limit timeout to 1 second.
            msg = consumer.poll(1.0)
            if msg is None:
                continue
            
            restaurant = json_deserializer(msg.value(), SerializationContext(msg.topic(), MessageField.VALUE))
            columns = list(restaurant.record)
            #df = pd.DataFrame(columns=columns)
            #df.to_csv("orders.csv",index=False)
            with open('orders.csv', 'a') as f_object:
              dictwriter_object = DictWriter(f_object, fieldnames=columns)
              dictwriter_object.writerow(restaurant.record)
              f_object.close()
            if restaurant is not None:
                print("User record {}: restaurant: {}\n"
                      .format(msg.key(), restaurant))
        except KeyboardInterrupt:
            break

    consumer.close()

main("restaurent-take-away-data")