import json
import requests
import sseclient
from azure.eventhub import EventHubProducerClient, EventData
import time

# Azure Event Hub bilgileri
CONNECTION_STR = "Endpoint=sb://wikinamespace.servicebus.windows.net/;SharedAccessKeyName=SendOnlyPolicy;SharedAccessKey="
EVENTHUB_NAME = "wikiEvents"


def get_stream():
    url = "https://stream.wikimedia.org/v2/stream/recentchange"
    headers = {"Accept": "text/event-stream"}
    response = requests.get(url, stream=True, headers=headers)

    # 💡 from_response yerine direkt response
    return sseclient.SSEClient(response)


def send_to_eventhub(producer, data):
    try:
        event_data = EventData(json.dumps(data))
        event_batch = producer.create_batch()
        event_batch.add(event_data)
        producer.send_batch(event_batch)
    except Exception as e:
        print("❌ Gönderme hatası:", e)


if __name__ == "__main__":
    print("📡 Wikipedia SSE akışına bağlanılıyor...")
    try:
        stream = get_stream()
        producer = EventHubProducerClient.from_connection_string(
            conn_str=CONNECTION_STR,
            eventhub_name=EVENTHUB_NAME
        )

        for event in stream.events():
            try:
                data = json.loads(event.data)
                filtered = {
                    "title": data.get("title"),
                    "user": data.get("user"),
                    "isBot": bool(data.get("bot")),
                    "comment": data.get("comment"),
                    "wiki": data.get("wiki"),
                    "timestamp": data.get("timestamp")
                }
                send_to_eventhub(producer, filtered)
                print(f"🚀 Gönderildi: {filtered['title']}")
                time.sleep(1)
            except Exception as e:
                print("Hata:", e)
    except Exception as e:
        print("❌ Bağlantı hatası:", e)