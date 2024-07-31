Türkçe:
Bu araç, https://github.com/fivexl/kubernetes-events-to-slack/tree/master GitHub deposundaki Kubernetes olaylarını Slack'e aktaran aracın güncellenmiş halidir. Kubernetes kümesindeki olayları Slack kanalına aktarmanızı sağlar. Slack web kancasını kullanarak, Kubernetes olaylarını Slack'e akışı sağlar ve herhangi bir belirteç gerektirmez. Yapılandırma, ortam değişkenleri aracılığıyla yapılır ve çeşitli seçenekler sunar (örneğin, belirli olayları filtreleme, kullanıcıları etiketleme vb.). Uygulama, Kubernetes ortamına kolay bir şekilde dağıtılabilir ve örnekler sağlanmıştır.

English:
This is an updated version of the tool available at https://github.com/fivexl/kubernetes-events-to-slack/tree/master. It allows you to stream Kubernetes events to a Slack channel. It uses Slack incoming webhooks to stream Kubernetes events to Slack without requiring any tokens. Configuration is done via environment variables and provides various options (e.g., filtering specific events, mentioning users, etc.). The application can be easily deployed to a Kubernetes environment, and example deployment files are provided.

### Yapılan Güncellemeler / Updates:

- **Eski Python Paketleri Güncellendi / Updated Old Python Packages:**
  Eski Python paketleri en son sürümlerine güncellendi. Bu, güvenlik açıklarını kapatır ve performansı artırır.
  - *Old Python packages have been updated to the latest versions. This addresses security vulnerabilities and improves performance.*

- **Koda Optimizasyonlar Yapıldı / Code Optimizations:**
  Kod bazında çeşitli optimizasyonlar gerçekleştirildi. Bu, uygulamanın genel hızını ve verimliliğini artırır.
  - *Various optimizations have been made in the codebase. This enhances the overall speed and efficiency of the application.*

- **Türkçeleştirildi. İngilizce Hali Çok Yakında Eklenecek / Localized to Turkish. English Version Coming Soon:**
  Uygulama tamamen Türkçeleştirildi. İngilizce sürümünün de çok yakında ekleneceğini belirtmek isteriz.
  - *The application has been fully localized to Turkish. We would like to inform you that the English version will be added soon.*

- **Mesaj Formatları Güncellendi / Updated Message Formats:**
  Gönderilen mesajların formatları yeniden düzenlendi. Bu, mesajların daha anlaşılır ve okunabilir olmasını sağlar.
  - *The formats of the sent messages have been reorganized. This makes the messages clearer and more readable.*

- **Dockerfile Düzenlendi ve Optimize Edildi / Dockerfile Tweaked and Optimized:**
  Dockerfile üzerinde düzenlemeler ve optimizasyonlar yapıldı. Bu, daha hızlı ve daha güvenilir bir yapı süreci sağlar.
  - *Tweaks and optimizations have been made to the Dockerfile. This ensures a faster and more reliable build process.*

### Eklenen Ekstra Özellikler / Added Extra Features:

- **Pod Durum Kontrolü / Pod Status Check:**
  Clusterınızda `running` durumunda olmayan bir pod varsa, sistem otomatik olarak Slack kanalınıza bir mesaj gönderir. Bu, sorunların hızlı bir şekilde fark edilmesini sağlar.
  - *If there is a pod in your cluster that is not in the `running` state, the system automatically sends a message to your Slack channel. This ensures that issues are quickly noticed.*

- **Zamanlayıcı / Scheduler:**
  Varsayılan olarak her 10 saniyede bir podların durumunu kontrol eder. Bu süre `K8S_EVENTS_STREAMER_POD_CHECK_INTERVAL` çevresel değişkeni ile özelleştirilebilir. Bu, sistemin esnekliğini artırır.
  - *By default, it checks the status of the pods every 10 seconds. This interval can be customized using the `K8S_EVENTS_STREAMER_POD_CHECK_INTERVAL` environment variable. This enhances the system's flexibility.*

# Konfigürasyon

Konfigürasyon, dağıtım veya configmap içindeki ortam değişkenleri aracılığıyla yapılır.

* `K8S_EVENTS_STREAMER_INCOMING_WEB_HOOK_URL` - Olayların gönderileceği Slack web hook URL'si. Zorunlu parametre.
* `K8S_EVENTS_STREAMER_NAMESPACE` - Olayların toplanacağı k8s namespace'i. Belirtilmezse tüm namespace'lerden gelen olaylar gönderilir.
* `K8S_EVENTS_STREAMER_DEBUG` - Günlüğe debug çıktıları yazmayı etkinleştir. Tanımlanmazsa `False`. Etkinleştirmek için `True` olarak ayarlayın.
* `K8S_EVENTS_STREAMER_SKIP_DELETE_EVENTS` - DELETED türündeki tüm olayları atlayın. Ortam değişkenini `True` olarak ayarlayarak etkinleştirin. Tanımlanmazsa `False`. Bu olaylar, k8s olayının silindiğini bildirdiği için operatör olarak size değer katmaz.
* `K8S_EVENTS_STREAMER_LIST_OF_REASONS_TO_SKIP` - Olayları `reason` (sebep) temelinde atlayın. Boşluklarla ayrılmış sebep listesi içermelidir. Çok fazla bilgi vermeyen olaylar olduğu için çok kullanışlıdır, örneğin image pulled veya replica scaled gibi. Tanımlanmazsa tüm olayları gönderir. Atlanması önerilen sebepler `'Scheduled ScalingReplicaSet Pulling Pulled Created Started Killing SuccessfulMountVolume SuccessfulUnMountVolume`. Daha fazla sebep görebilirsiniz [burada](https://github.com/kubernetes/kubernetes/blob/master/pkg/kubelet/events/event.go).
* `K8S_EVENTS_STREAMER_USERS_TO_NOTIFY` - Uyarı olaylarında kullanıcıları mention yapın, örneğin `<@andrey9kin> <@slackbot>`. Not! Kullanıcı adının etrafında `<>` kullanmanız önemlidir. Daha fazla bilgi için [buraya](https://api.slack.com/docs/message-formatting#linking_to_channels_and_users) bakın.
* `K8S_EVENTS_STREAMER_LOG_LEVEL` - Günlük seviyesini ayarlayın. Örneğin `INFO`, `DEBUG`, `WARN`. Tanımlanmazsa `INFO` olarak ayarlanır.
  
# Configuration

Configuration is done via env variables that you set in deployment or configmap.

* `K8S_EVENTS_STREAMER_INCOMING_WEB_HOOK_URL` - Slack web hook URL where to send events. Mandatory parameter.
* `K8S_EVENTS_STREAMER_NAMESPACE` - k8s namespace to collect events from. Will use be sending events from all namespaces if not specified
* `K8S_EVENTS_STREAMER_DEBUG` - Enable debug print outs to the log. `False` if not defined. Set to `True` to enable.
* `K8S_EVENTS_STREAMER_SKIP_DELETE_EVENTS` - Skip all events of type DELETED by setting  env variable to `True`. `False` if not defined. Very useful since those events tells you that k8s event was deleted which has no value to you as operator.
* `K8S_EVENTS_STREAMER_LIST_OF_REASONS_TO_SKIP` - Skip events based on their `reason`. Should contain list of reasons separated by spaces. Very useful since there are a lot of events that doesn't tell you much like image pulled or replica scaled. Send all events if not defined. Recommended reasons to skip `'Scheduled ScalingReplicaSet Pulling Pulled Created Started Killing SuccessfulMountVolume SuccessfulUnMountVolume`. You can see more reasons [here](https://github.com/kubernetes/kubernetes/blob/master/pkg/kubelet/events/event.go)
* `K8S_EVENTS_STREAMER_USERS_TO_NOTIFY` - Mention users on warning events, ex `<@andrey9kin> <@slackbot>`. Note! It is important that you use `<>` around user name. Read more [here](https://api.slack.com/docs/message-formatting#linking_to_channels_and_users)

# Deployment

Kubernetes kümenizde `deployment.yaml` dosyasını çalıştırarak aracı deneyebilirsiniz. 
Çalıştırmak için build ettiğiniz Docker imajınızı ve Slack Webhook URL bilgilerinizi girmeniz gerekir.

You can try the tool by running the `deployment.yaml` file in your Kubernetes cluster. 
Please enter the Docker image you built and your Slack Webhook URL to run it.

# Örnek Mesajlar / Example Messages
![image](https://github.com/user-attachments/assets/d20f2c43-ebb0-4535-9992-91bde6f5e491)

![image](https://github.com/user-attachments/assets/584e7b78-6b2e-450c-a46b-1bb3613850e3)

