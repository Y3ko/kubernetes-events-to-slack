#!/usr/bin/env python3

import os
import sys
import time
import json
import logging
import traceback
import requests
from kubernetes import client, config, watch
from kubernetes.client import CustomObjectsApi

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def read_env_variable_or_die(env_var_name):
    value = os.environ.get(env_var_name, '')
    if not value:
        message = f'{env_var_name} isimli ortam değişkeni tanımlanmamış veya boş bir değer olarak ayarlanmış. '
        message += 'Lütfen bu değeri dolu bir string ile ayarlayıp tekrar deneyin.'
        logger.error(message)
        raise EnvironmentError(message)
    return value

def post_slack_message(hook_url, message):
    logger.info(f'Aşağıdaki mesaj gönderiliyor:\n{message}')
    headers = {'Content-Type': 'application/json'}
    response = requests.post(hook_url, headers=headers, data=message)
    if response.status_code != 200:
        logger.error(f"Slack'e mesaj gönderilemedi: {response.status_code}, {response.text}")
    else:
        logger.info(f"Mesaj başarıyla Slack'e gönderildi.")

def get_event_reason(event):
    """ CoreV1Event nesnesinin doğrudan erişimi """
    return event.reason.upper() if event.reason else 'UNKNOWN'

def format_k8s_event_to_slack_message(event_object, notify=''):
    event = event_object['object']
    message = {
        'attachments': [{
            'color': '#36a64f',  # Yeşil (Normal olaylar)
            'title': event.message if event.message else 'Mesaj yok',
            'text': f"Etkinlik türü: {event_object['type'] if event_object['type'] else 'Bilinmiyor'}, "
                    f"Etkinlik nedeni: {event.reason if event.reason else 'Bilinmiyor'}",
            'footer': f"İlk görülme: {event.first_timestamp if event.first_timestamp else 'Bilgi yok'}, "
                      f"Son görülme: {event.last_timestamp if event.last_timestamp else 'Bilgi yok'}, "
                      f"Sayım: {event.count if event.count else 'Bilgi yok'}",
            'fields': [
                {
                    'title': 'İlgili nesne',
                    'value': f"Tür: {event.involved_object.kind if event.involved_object.kind else 'Bilinmiyor'}, "
                             f"Ad: {event.involved_object.name if event.involved_object.name else 'Bilinmiyor'}, "
                             f"Namespace: {event.involved_object.namespace if event.involved_object.namespace else 'Bilinmiyor'}",
                    'short': 'true'
                },
                {
                    'title': 'Metadata',
                    'value': f"Ad: {event.metadata.name if event.metadata.name else 'Bilinmiyor'}, "
                             f"Oluşturma zamanı: {event.metadata.creation_timestamp if event.metadata.creation_timestamp else 'Bilgi yok'}",
                    'short': 'true'
                }
            ],
        }]
    }

    event_reason = get_event_reason(event)

    if event_reason in ['KILLING', 'FAILED', 'BACKOFF', 'UNHEALTHY', 'CREATEFAILED', 'DELETED', 'TOPCONNECTIONFAILED', 'NODEHASNODISKPRESSURE']:
        message['attachments'][0]['color'] = '#cc0000'  # Kırmızı (Kritik hatalar)
    elif event.type.upper() in ['PULLING', 'SCALINGREPLICASET', 'SCHEDULED', 'NOTRECONCILINGDRAIN', 'EVICTIONTHRESHOLDMET']:
        message['attachments'][0]['color'] = '#ffcc00'  # Sarı (Orta düzeydeki hatalar)
        if notify:
            message['text'] = f'{notify}, kontrol etmeniz gereken bir uyarı var'
    elif event.type.upper() == 'WARNING':
        message['attachments'][0]['color'] = '#ffcc00'  # Sarı (Orta düzeydeki hatalar)
        if notify:
            message['text'] = f'{notify}, kontrol etmeniz gereken bir uyarı var'

    return json.dumps(message)

def format_error_to_slack_message(error_message):
    message = {
        'attachments': [{
            'color': '#8963B9',
            'title': 'Hata Bildirimi',
            'text': f'Logları kontrol edin! Hata ile olaylar işlenemedi: {error_message}'
        }]
    }
    return json.dumps(message)

def stream_events(k8s_client, k8s_namespace_name, timeout):
    v1 = k8s_client.CoreV1Api()
    k8s_watch = watch.Watch()
    if k8s_namespace_name:
        return k8s_watch.stream(v1.list_namespaced_event, namespace=k8s_namespace_name, timeout_seconds=timeout)
    else:
        return k8s_watch.stream(v1.list_event_for_all_namespaces, timeout_seconds=timeout)

def handle_event(event, reasons_to_skip, users_to_notify, slack_web_hook_url, cached_event_uids):
    try:
        logger.debug(str(event))
        event_obj = event['object']
        event_reason = get_event_reason(event_obj)
        event_uid = event_obj.metadata.uid
        if event_reason in reasons_to_skip:
            logger.info(f'Etkinlik nedeni {event_reason} ve atlanacak nedenler listesinde. Atlanıyor.')
            return
        if event_uid in cached_event_uids:
            logger.info(f'Etkinlik kimliği {event_uid} ve önbellekteki etkinlikler listesinde. Atlanıyor.')
            return
        message = format_k8s_event_to_slack_message(event, users_to_notify)
        post_slack_message(slack_web_hook_url, message)
        cached_event_uids.append(event_uid)
    except Exception as error:
        logger.exception(error)
        stack_trace = traceback.format_exc()
        message = f'Olayı işleyemedik, hata:\n{stack_trace}\n{event}'
        post_slack_message(slack_web_hook_url, format_error_to_slack_message(message))
        time.sleep(30)

def send_pod_list_to_slack(k8s_client, k8s_namespace_name, slack_web_hook_url, stable_system_message_sent):
    v1 = k8s_client.CoreV1Api()
    try:
        if k8s_namespace_name:
            pods = v1.list_namespaced_pod(namespace=k8s_namespace_name)
        else:
            pods = v1.list_pod_for_all_namespaces()

        pod_list = []
        all_pods_running = True
        for pod in pods.items:
            # Pod phase kontrolü
            if pod.status.phase != "Running":
                pod_list.append(f"Pod Adı: {pod.metadata.name}, Namespace: {pod.metadata.namespace}, Durum: {pod.status.phase}")
                all_pods_running = False

            # Container status kontrolü
            if pod.status.container_statuses:
                for container_status in pod.status.container_statuses:
                    if container_status.state.waiting and container_status.state.waiting.reason in ["CrashLoopBackOff", "OOMKilled"]:
                        pod_list.append(f"Pod Adı: {pod.metadata.name}, Namespace: {pod.metadata.namespace}, Durum: {container_status.state.waiting.reason}")
                        all_pods_running = False

        if all_pods_running and not stable_system_message_sent:
            message = {
                'attachments': [{
                    'color': '#36a64f',  # Yeşil (Stabil sistem)
                    'title': 'Sistem Stabil',
                    'text': 'Tüm podlar "Running" durumunda.',
                    'footer': 'Pod Listesi',
                }]
            }
            post_slack_message(slack_web_hook_url, json.dumps(message))
            stable_system_message_sent = True
        elif not all_pods_running:
            stable_system_message_sent = False
            message = {
                'attachments': [{
                    'color': '#cc0000',  # Kırmızı (Uyarı olayları)
                    'title': 'RUNNING DURUMUNDA OLMAYAN POD LISTESI',
                    'text': '\n'.join(pod_list),
                    'footer': 'Pod Listesi',
                }]
            }
            post_slack_message(slack_web_hook_url, json.dumps(message))
    except Exception as e:
        logger.error(f"Pod listesini Slack'e gönderirken hata oluştu: {e}")
        stack_trace = traceback.format_exc()
        message = f'Pod listesini Slack\'e gönderirken hata oluştu:\n{stack_trace}'
        post_slack_message(slack_web_hook_url, format_error_to_slack_message(message))
    return stable_system_message_sent

def main():
    logging.basicConfig(stream=sys.stdout, level=logging.DEBUG if os.environ.get('K8S_EVENTS_STREAMER_DEBUG', False) else logging.INFO,
                        format='%(asctime)s %(levelname)-8s %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

    logger.info('Konfigürasyon okunuyor...')
    k8s_namespace_name = os.environ.get('K8S_EVENTS_STREAMER_NAMESPACE', '')
    reasons_to_skip = os.environ.get('K8S_EVENTS_STREAMER_LIST_OF_REASONS_TO_SKIP', '').upper().split()
    skip_delete_events = os.environ.get('K8S_EVENTS_STREAMER_SKIP_DELETE_EVENTS', '').lower() == 'true'
    last_pod_check_time = time.time()
    if skip_delete_events:
        logger.info('SUCCESSFULDELETE, atlanacak nedenler listesine eklendi')
        reasons_to_skip.append('SUCCESSFULDELETE')
    users_to_notify = os.environ.get('K8S_EVENTS_STREAMER_USERS_TO_NOTIFY', '')
    slack_web_hook_url = read_env_variable_or_die('K8S_EVENTS_STREAMER_INCOMING_WEB_HOOK_URL')
    pod_check_interval = 10  # 10 saniye olarak ayarlandı

    logger.info('Konfigürasyon tamam')
    logger.info('Aşağıdaki parametrelerle çalışıyor')
    logger.info(f'K8S_EVENTS_STREAMER_NAMESPACE: {k8s_namespace_name}')
    logger.info(f'K8S_EVENTS_STREAMER_LIST_OF_REASONS_TO_SKIP: {reasons_to_skip}')
    logger.info(f'K8S_EVENTS_STREAMER_USERS_TO_NOTIFY: {users_to_notify}')
    logger.info(f'K8S_EVENTS_STREAMER_INCOMING_WEB_HOOK_URL: {slack_web_hook_url}')
    logger.info(f'K8S_EVENTS_STREAMER_POD_CHECK_INTERVAL: {pod_check_interval} saniye')

    logger.info('K8s yapılandırması yükleniyor...')
    config.load_incluster_config()

    # Mevcut pod listesini Slack'e gönder
    stable_system_message_sent = False
    stable_system_message_sent = send_pod_list_to_slack(client, k8s_namespace_name, slack_web_hook_url, stable_system_message_sent)

    cached_event_uids = []
    while True:
        try:
            logger.info('İki saat boyunca olaylar işleniyor...')
            for event in stream_events(client, k8s_namespace_name, 7200):
                handle_event(event, reasons_to_skip, users_to_notify, slack_web_hook_url, cached_event_uids)

                # Check if 5 seconds have passed since the last pod check
                if time.time() - last_pod_check_time >= pod_check_interval:
                    stable_system_message_sent = send_pod_list_to_slack(client, k8s_namespace_name, slack_web_hook_url, stable_system_message_sent)
                    last_pod_check_time = time.time()

        except TimeoutError as timeout_error:
            logger.exception(timeout_error)
            logger.warning('Zaman aşımı hatası nedeniyle 30 saniye bekleyin ve tekrar kontrol edin.')
            time.sleep(30)
        except Exception as error:
            logger.exception(error)
            stack_trace = traceback.format_exc()
            message = f'Beklenmeyen hata:\n{stack_trace}'
            post_slack_message(slack_web_hook_url, format_error_to_slack_message(message))
            time.sleep(30)

        cached_event_uids = []

    logger.info('Tamamlandı')

if __name__ == '__main__':
    main()
