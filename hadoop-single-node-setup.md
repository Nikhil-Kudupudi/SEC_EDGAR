# Single-Node Hadoop 3.3.x Installation Guide (Ubuntu 24.04)

This README provides a streamlined guide to installing and configuring Apache Hadoop in Pseudo-Distributed Mode on a single Ubuntu machine.

---

## Prerequisites & Dependencies

Ensure your system package list is updated and the full Java 17 Development Kit (which includes `jps`) along with SSH utilities are installed:

```bash
sudo apt update
sudo apt install openjdk-17-jdk-headless openssh-server openssh-client -y
```

---

## 1. Configure Passwordless SSH
Hadoop requires passwordless SSH access to manage its daemons on `localhost`.

1. Generate an RSA key pair (Press **Enter** to accept defaults):
   ```bash
   ssh-keygen -t rsa -P "" -f ~/.ssh/id_rsa
   ```
2. Authorize the public key:
   ```bash
   cat ~/.ssh/id_rsa.pub >> ~/.ssh/authorized_keys
   chmod 0600 ~/.ssh/authorized_keys
   ```
3. Test the connection (type `yes` if prompted, then `exit`):
   ```bash
   ssh localhost
   ```

---

## 2. Download and Place Hadoop
1. Download the binaries (adjust the version string if using a newer release):
   ```bash
   wget https://apache.org
   ```
2. Extract and move to global space:
   ```bash
   tar -xzvf hadoop-3.3.6.tar.gz
   sudo mv hadoop-3.3.6 /usr/local/hadoop
   ```
3. **Crucial Permission Fix:** Grant your user full ownership of the directory to avoid "Permission Denied" crashes:
   ```bash
   sudo chown -R $USER:$USER /usr/local/hadoop
   ```

---

## 3. Environment Variables (`~/.bashrc`)
Open your profile: `nano ~/.bashrc` and paste the following block at the very bottom:

```bash
# Hadoop Environment Variables
export JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64
export HADOOP_HOME=/usr/local/hadoop
export HADOOP_INSTALL=$HADOOP_HOME
export HADOOP_MAPRED_HOME=$HADOOP_HOME
export HADOOP_COMMON_HOME=$HADOOP_HOME
export HADOOP_HDFS_HOME=$HADOOP_HOME
export YARN_HOME=$HADOOP_HOME
export HADOOP_COMMON_LIB_NATIVE_DIR=$HADOOP_HOME/lib/native
export PATH=$PATH:$HADOOP_HOME/sbin:$HADOOP_HOME/bin:$JAVA_HOME/bin
export HADOOP_OPTS="-Djava.library.path=$HADOOP_HOME/lib/native"
```
Apply the environment updates immediately:
```bash
source ~/.bashrc
```

---

## 4. Configuration Files (`/usr/local/hadoop/etc/hadoop/`)

### hadoop-env.sh
Open the file: `nano /usr/local/hadoop/etc/hadoop/hadoop-env.sh`
Find or add the explicit Java path line:
```bash
export JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64
```

### core-site.xml
Add inside the `<configuration>` tags:
```xml
<property>
    <name>fs.defaultFS</name>
    <value>hdfs://localhost:9000</value>
</property>
```

### hdfs-site.xml
Add inside the `<configuration>` tags (Forces single replication and sets storage directories):
```xml
<property>
    <name>dfs.replication</name>
    <value>1</value>
</property>
<property>
    <name>dfs.namenode.name.dir</name>
    <value>file:///usr/local/hadoop/hadoop_data/hdfs/namenode</value>
</property>
<property>
    <name>dfs.datanode.data.dir</name>
    <value>file:///usr/local/hadoop/hadoop_data/hdfs/datanode</value>
</property>
```

### mapred-site.xml
Add inside the `<configuration>` tags:
```xml
<property>
    <name>mapreduce.framework.name</name>
    <value>yarn</value>
</property>
```

### yarn-site.xml
Add inside the `<configuration>` tags:
```xml
<property>
    <name>yarn.nodemanager.aux-services</name>
    <value>mapreduce_shuffle</value>
</property>
```

---

## 5. First-Time Initialization & Startup

1. **Format the NameNode FileSystem** (Only run this *once* during initial setup):
   ```bash
   hdfs namenode -format
   ```
2. **Start the Cluster Daemons:**
   ```bash
   start-dfs.sh
   start-yarn.sh
   ```
3. **Verify running processes:**
   ```bash
   jps
   ```
   *Expected output: NameNode, DataNode, SecondaryNameNode, ResourceManager, NodeManager, Jps.*

---

## 6. Cluster Management Commands

* **Stop the Cluster:** `stop-yarn.sh && stop-dfs.sh`
* **Start the Cluster:** `start-dfs.sh && start-yarn.sh`
* **HDFS Web Console:** [http://localhost:9870](http://localhost:9870)
* **YARN Applications Monitor:** [http://localhost:8088](http://localhost:8088)
