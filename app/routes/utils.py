"""Utils for Routes."""
import datetime
# import os.path
#
# from qpylib import qpylib
# import requests
# import socket
#
# from OpenSSL import SSL
# from cryptography.hazmat.primitives import serialization

from app.constants.general import (
    C_LEVEL_UNKNOWN,
    DOMAIN,
    EMAIL,
    END_TIME,
    HIGH,
    I_TYPE_ALL,
    IPV4,
    LOW,
    MD5_HASH,
    MEDIUM,
    SELECT_LEVEL,
    SELECT_TYPE,
    START_TIME,
    URI, LOG_LEVEL_DEBUG, CERT_FILE, LOG_LEVEL_INFO,
)
from app.constants.messages import FETCH_CERTIFICATES, WRITING_CERTIFICATE_PATH, ERROR_IN_FETCHING_CERTIFICATE


def prepare_observable_data(data):
    """Prepare Observable data to show on UI.

    :param data: Observable data
    :type data: dict
    :return: Only selected fields dict
    :rtype: dict
    """
    new_data = {}
    new_data["type"] = data.get("type")
    new_data["value"] = data.get("value")
    new_data["classification"] = data.get("meta").get("maliciousness")
    return new_data


def prepare_entity_data(data, obs_data):
    """Prepare entity data to show on UI.

    :param data: Entity data
    :type data: dict
    :param data: Observable data
    :type data: list
    :return: Only selected fields dict
    :rtype: dict
    """
    new_data = {}
    if data.get("data"):
        new_data["title"] = (
            data.get("data").get("title") if data.get("data").get("title") else ""
        )
        new_data["confidence"] = (
            data.get("data").get("confidence")
            if data.get("data").get("confidence")
            else ""
        )
        new_data["description"] = (
            data.get("data").get("description")
            if data.get("data").get("description")
            else ""
        )
        if data.get("data").get("producer"):
            new_data["source_name"] = (
                data.get("data").get("producer").get("identity")
                if data.get("data").get("producer").get("identity")
                else ""
            )
        else:
            new_data["source_name"] = ""
        new_data["observables"] = obs_data
    if data.get("meta"):
        new_data["threat_start_time"] = (
            data.get("meta").get("estimated_threat_start_time")
            if data.get("meta").get("estimated_threat_start_time")
            else ""
        )
        new_data["tags"] = (
            ",".join(data.get("meta").get("tags"))
            if data.get("meta").get("tags")
            else ""
        )
    return new_data


def get_entity_data(data_item, eiq_api):
    """Get entity data to show on UI.

    :param data_item: Data from lookup obsrvables Dict
    :type data_item: dict
    :param eiq_api: EIQ API object
    :type eiq_api: object
    :return: prepared data to show on UI
    :rtype: dict
    """
    entity_data_dict = []
    for item in data_item.get("entities"):
        entity_data = eiq_api.fetch_entity_details(str(item.split("/")[-1]))
        observables = (
            entity_data.get("observables") if entity_data.get("observables") else []
        )
        obs_data_list = []
        for observable in observables:
            obs_data = eiq_api.get_observable_by_id(str(observable.split("/")[-1]))

            append_data = prepare_observable_data(obs_data)

            obs_data_list.append(append_data)
        if entity_data:
            entity_data_dict.append(prepare_entity_data(entity_data, obs_data_list))
    return entity_data_dict


def get_filters(i_type, c_level, time):
    """Get filters for use in sql query.

    :param i_type: indicator type selected by user
    :type i_type: str
    :param c_level: confidence level selected by user
    :type c_level: str
    :param time: timestamp selected by user
    :type time: str
    :return: dict of filters applied
    :rtype: dict
    """
    filters = {}
    if i_type == I_TYPE_ALL:
        select_type = (IPV4, MD5_HASH, DOMAIN, URI, EMAIL)
    else:
        select_type = "('" + i_type + "')"
    if c_level == C_LEVEL_UNKNOWN:
        select_level = (C_LEVEL_UNKNOWN, LOW, MEDIUM, HIGH)
    elif c_level == LOW:
        select_level = (LOW, MEDIUM, HIGH)
    elif c_level == MEDIUM:
        select_level = (MEDIUM, HIGH)
    else:
        select_level = "('high')"
    if time.endswith("h"):
        start_time = int(
            (
                    datetime.datetime.now() - datetime.timedelta(hours=int(time[:-1]))
            ).timestamp()
        )
    elif time.endswith("d"):
        start_time = int(
            (
                    datetime.datetime.now() - datetime.timedelta(days=int(time[:-1]))
            ).timestamp()
        )
    elif time.endswith("m"):
        start_time = int(
            (
                    datetime.datetime.now() - datetime.timedelta(minutes=int(time[:-1]))
            ).timestamp()
        )
    filters[END_TIME] = int(datetime.datetime.now().timestamp())
    filters[START_TIME] = start_time
    filters[SELECT_TYPE] = select_type
    filters[SELECT_LEVEL] = select_level
    return filters

#
# def get_unverified_cert(host, port, pem_path):
#     qpylib.log(FETCH_CERTIFICATES.format(host, port))
#     try:
#         context = SSL.Context(SSL.TLSv1_2_METHOD)
#         context.set_cipher_list('ALL:@SECLEVEL=0'.encode('utf-8'))
#
#         conn = SSL.Connection(context, socket=socket.socket(socket.AF_INET, socket.SOCK_STREAM))
#         conn.set_tlsext_host_name(host.encode())
#         conn.settimeout(5)
#         conn.connect((host, port))
#         conn.setblocking(1)
#         conn.do_handshake()
#
#         for (idx, cert) in enumerate(conn.get_peer_cert_chain()):
#             qpylib.log(f'{idx} subject: {cert.get_subject()}', level=LOG_LEVEL_DEBUG)
#             qpylib.log(f'  issuer: {cert.get_issuer()})', level=LOG_LEVEL_DEBUG)
#             qpylib.log(f'  fingerprint: {cert.digest("sha1")}', level=LOG_LEVEL_DEBUG)
#
#         conn.close()
#
#         # save the cert chain as a pem file
#
#         with open(os.path.join(pem_path, CERT_FILE), 'ba') as f:
#             f.truncate(0)
#             for (idx, cert) in enumerate(conn.get_peer_cert_chain()):
#                 qpylib.log(WRITING_CERTIFICATE_PATH.format(idx, pem_path), level=LOG_LEVEL_INFO)
#                 pem_bytes = cert.to_cryptography().public_bytes(serialization.Encoding.PEM)
#                 f.write(pem_bytes)
#                 f.write(b"\n")
#     except Exception as error:
#         qpylib.log(ERROR_IN_FETCHING_CERTIFICATE.format(error))