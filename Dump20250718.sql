-- MySQL dump 10.13  Distrib 8.0.40, for Win64 (x86_64)
--
-- Host: localhost    Database: railway
-- ------------------------------------------------------
-- Server version	8.0.40

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `act_expense`
--

DROP TABLE IF EXISTS `act_expense`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `act_expense` (
  `act_expense_id` int NOT NULL AUTO_INCREMENT,
  `act_expense_date` date DEFAULT NULL,
  `act_expense_description` varchar(55) DEFAULT NULL,
  `act_expense_amount` decimal(6,2) DEFAULT NULL,
  `act_expense_approved` varchar(3) DEFAULT NULL,
  `act_expense_paid` varchar(3) DEFAULT NULL,
  `prop_id` int NOT NULL,
  `act_expense_document` varchar(100) DEFAULT NULL,
  PRIMARY KEY (`act_expense_id`),
  KEY `act_expense_prop_id_a022b71e_fk_prop_prop_id` (`prop_id`),
  CONSTRAINT `act_expense_prop_id_a022b71e_fk_prop_prop_id` FOREIGN KEY (`prop_id`) REFERENCES `prop` (`prop_id`)
) ENGINE=InnoDB AUTO_INCREMENT=24 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `act_expense`
--

LOCK TABLES `act_expense` WRITE;
/*!40000 ALTER TABLE `act_expense` DISABLE KEYS */;
INSERT INTO `act_expense` VALUES (1,'2025-04-22','Paid Mathew for Repairs',200.00,'Yes','Yes',1,NULL),(2,'2025-05-18','Kyrio Vangeli - Eleftheroupoleos',100.00,'Yes','Yes',3,''),(3,'2024-08-01','XXXXX',500.00,'No','No',11,NULL),(4,'2024-09-11','YYYYY',999.00,'No','No',10,NULL),(5,'2025-04-13','ZZZZZZZZZZZZZ',133.00,'Yes','Yes',1,NULL),(6,'2025-05-21','BBBBBBBBBBBB',872.00,'Yes','Yes',5,'expense_docs/pindarou-20250521-Invoice.pdf'),(7,'2025-05-14','rrrrrrrrrrrrrrrrrrrrrrrrrrrrr',1188.00,'Yes','No',2,'expense_docs/foti-pitta-20250514-Invoice.pdf'),(11,'2025-05-14','ttttttttttttttttttttttttttttttttttt',456.00,'No','No',4,''),(12,'2025-05-08','fffffffffffffffffffffffffffff',354.00,'Yes','Yes',7,''),(13,'2025-05-20','qwerty',1234.00,'Yes','Yes',7,''),(14,'2025-05-05','Test Expense for Approval',765.00,'Yes','Yes',7,NULL),(15,'2024-12-04','Demetri Expense',135.00,'Yes','Yes',9,NULL),(16,'2024-11-01','Stella\'s Expense',246.00,'Yes','Yes',2,NULL),(17,'2025-05-06','Test Expense',4000.00,'No','No',5,NULL),(21,'2025-06-20','New Expense',123.00,'Yes','Yes',1,'expense_docs/palikaridi-20250620-ΤΠΥ_ΑΓΓΕΛΑΤΟΣ.pdf'),(22,'2025-06-30','New Test Expense',100.00,'No','No',3,'expense_docs/pindarou-20250630-Invoice.pdf'),(23,'2025-06-30','wwwwwwwwwwwwwwwwww',1111.00,'No','No',1,'');
/*!40000 ALTER TABLE `act_expense` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `auth_group`
--

DROP TABLE IF EXISTS `auth_group`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `auth_group` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(150) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `auth_group`
--

LOCK TABLES `auth_group` WRITE;
/*!40000 ALTER TABLE `auth_group` DISABLE KEYS */;
/*!40000 ALTER TABLE `auth_group` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `auth_group_permissions`
--

DROP TABLE IF EXISTS `auth_group_permissions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `auth_group_permissions` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `group_id` int NOT NULL,
  `permission_id` int NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `auth_group_permissions_group_id_permission_id_0cd325b0_uniq` (`group_id`,`permission_id`),
  KEY `auth_group_permissio_permission_id_84c5c92e_fk_auth_perm` (`permission_id`),
  CONSTRAINT `auth_group_permissio_permission_id_84c5c92e_fk_auth_perm` FOREIGN KEY (`permission_id`) REFERENCES `auth_permission` (`id`),
  CONSTRAINT `auth_group_permissions_group_id_b120cbf9_fk_auth_group_id` FOREIGN KEY (`group_id`) REFERENCES `auth_group` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `auth_group_permissions`
--

LOCK TABLES `auth_group_permissions` WRITE;
/*!40000 ALTER TABLE `auth_group_permissions` DISABLE KEYS */;
/*!40000 ALTER TABLE `auth_group_permissions` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `auth_permission`
--

DROP TABLE IF EXISTS `auth_permission`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `auth_permission` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(255) NOT NULL,
  `content_type_id` int NOT NULL,
  `codename` varchar(100) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `auth_permission_content_type_id_codename_01ab375a_uniq` (`content_type_id`,`codename`),
  CONSTRAINT `auth_permission_content_type_id_2f476e4b_fk_django_co` FOREIGN KEY (`content_type_id`) REFERENCES `django_content_type` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=113 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `auth_permission`
--

LOCK TABLES `auth_permission` WRITE;
/*!40000 ALTER TABLE `auth_permission` DISABLE KEYS */;
INSERT INTO `auth_permission` VALUES (1,'Can add log entry',1,'add_logentry'),(2,'Can change log entry',1,'change_logentry'),(3,'Can delete log entry',1,'delete_logentry'),(4,'Can view log entry',1,'view_logentry'),(5,'Can add permission',2,'add_permission'),(6,'Can change permission',2,'change_permission'),(7,'Can delete permission',2,'delete_permission'),(8,'Can view permission',2,'view_permission'),(9,'Can add group',3,'add_group'),(10,'Can change group',3,'change_group'),(11,'Can delete group',3,'delete_group'),(12,'Can view group',3,'view_group'),(13,'Can add user',4,'add_user'),(14,'Can change user',4,'change_user'),(15,'Can delete user',4,'delete_user'),(16,'Can view user',4,'view_user'),(17,'Can add content type',5,'add_contenttype'),(18,'Can change content type',5,'change_contenttype'),(19,'Can delete content type',5,'delete_contenttype'),(20,'Can view content type',5,'view_contenttype'),(21,'Can add session',6,'add_session'),(22,'Can change session',6,'change_session'),(23,'Can delete session',6,'delete_session'),(24,'Can view session',6,'view_session'),(25,'Can add properties',7,'add_properties'),(26,'Can change properties',7,'change_properties'),(27,'Can delete properties',7,'delete_properties'),(28,'Can view properties',7,'view_properties'),(29,'Can add props',8,'add_props'),(30,'Can change props',8,'change_props'),(31,'Can delete props',8,'delete_props'),(32,'Can view props',8,'view_props'),(33,'Can add petty',9,'add_petty'),(34,'Can change petty',9,'change_petty'),(35,'Can delete petty',9,'delete_petty'),(36,'Can view petty',9,'view_petty'),(37,'Can add invoices',10,'add_invoices'),(38,'Can change invoices',10,'change_invoices'),(39,'Can delete invoices',10,'delete_invoices'),(40,'Can view invoices',10,'view_invoices'),(41,'Can add issues',11,'add_issues'),(42,'Can change issues',11,'change_issues'),(43,'Can delete issues',11,'delete_issues'),(44,'Can view issues',11,'view_issues'),(45,'Can add issues_details',12,'add_issues_details'),(46,'Can change issues_details',12,'change_issues_details'),(47,'Can delete issues_details',12,'delete_issues_details'),(48,'Can view issues_details',12,'view_issues_details'),(49,'Can add tenant',13,'add_tenant'),(50,'Can change tenant',13,'change_tenant'),(51,'Can delete tenant',13,'delete_tenant'),(52,'Can view tenant',13,'view_tenant'),(53,'Can add supplier',14,'add_supplier'),(54,'Can change supplier',14,'change_supplier'),(55,'Can delete supplier',14,'delete_supplier'),(56,'Can view supplier',14,'view_supplier'),(57,'Can add crontab',15,'add_crontabschedule'),(58,'Can change crontab',15,'change_crontabschedule'),(59,'Can delete crontab',15,'delete_crontabschedule'),(60,'Can view crontab',15,'view_crontabschedule'),(61,'Can add interval',16,'add_intervalschedule'),(62,'Can change interval',16,'change_intervalschedule'),(63,'Can delete interval',16,'delete_intervalschedule'),(64,'Can view interval',16,'view_intervalschedule'),(65,'Can add periodic task',17,'add_periodictask'),(66,'Can change periodic task',17,'change_periodictask'),(67,'Can delete periodic task',17,'delete_periodictask'),(68,'Can view periodic task',17,'view_periodictask'),(69,'Can add periodic task track',18,'add_periodictasks'),(70,'Can change periodic task track',18,'change_periodictasks'),(71,'Can delete periodic task track',18,'delete_periodictasks'),(72,'Can view periodic task track',18,'view_periodictasks'),(73,'Can add solar event',19,'add_solarschedule'),(74,'Can change solar event',19,'change_solarschedule'),(75,'Can delete solar event',19,'delete_solarschedule'),(76,'Can view solar event',19,'view_solarschedule'),(77,'Can add clocked',20,'add_clockedschedule'),(78,'Can change clocked',20,'change_clockedschedule'),(79,'Can delete clocked',20,'delete_clockedschedule'),(80,'Can view clocked',20,'view_clockedschedule'),(81,'Can add prop_values',21,'add_prop_values'),(82,'Can change prop_values',21,'change_prop_values'),(83,'Can delete prop_values',21,'delete_prop_values'),(84,'Can view prop_values',21,'view_prop_values'),(85,'Can add revenue',22,'add_revenue'),(86,'Can change revenue',22,'change_revenue'),(87,'Can delete revenue',22,'delete_revenue'),(88,'Can view revenue',22,'view_revenue'),(89,'Can add revenue_line_types',23,'add_revenue_line_types'),(90,'Can change revenue_line_types',23,'change_revenue_line_types'),(91,'Can delete revenue_line_types',23,'delete_revenue_line_types'),(92,'Can view revenue_line_types',23,'view_revenue_line_types'),(93,'Can add revenue_types',24,'add_revenue_types'),(94,'Can change revenue_types',24,'change_revenue_types'),(95,'Can delete revenue_types',24,'delete_revenue_types'),(96,'Can view revenue_types',24,'view_revenue_types'),(97,'Can add expense_line_types',25,'add_expense_line_types'),(98,'Can change expense_line_types',25,'change_expense_line_types'),(99,'Can delete expense_line_types',25,'delete_expense_line_types'),(100,'Can view expense_line_types',25,'view_expense_line_types'),(101,'Can add expense_types',26,'add_expense_types'),(102,'Can change expense_types',26,'change_expense_types'),(103,'Can delete expense_types',26,'delete_expense_types'),(104,'Can view expense_types',26,'view_expense_types'),(105,'Can add expense',27,'add_expense'),(106,'Can change expense',27,'change_expense'),(107,'Can delete expense',27,'delete_expense'),(108,'Can view expense',27,'view_expense'),(109,'Can add act_expense',28,'add_act_expense'),(110,'Can change act_expense',28,'change_act_expense'),(111,'Can delete act_expense',28,'delete_act_expense'),(112,'Can view act_expense',28,'view_act_expense');
/*!40000 ALTER TABLE `auth_permission` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `auth_user`
--

DROP TABLE IF EXISTS `auth_user`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `auth_user` (
  `id` int NOT NULL AUTO_INCREMENT,
  `password` varchar(128) NOT NULL,
  `last_login` datetime(6) DEFAULT NULL,
  `is_superuser` tinyint(1) NOT NULL,
  `username` varchar(150) NOT NULL,
  `first_name` varchar(150) NOT NULL,
  `last_name` varchar(150) NOT NULL,
  `email` varchar(254) NOT NULL,
  `is_staff` tinyint(1) NOT NULL,
  `is_active` tinyint(1) NOT NULL,
  `date_joined` datetime(6) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `username` (`username`)
) ENGINE=InnoDB AUTO_INCREMENT=6 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `auth_user`
--

LOCK TABLES `auth_user` WRITE;
/*!40000 ALTER TABLE `auth_user` DISABLE KEYS */;
INSERT INTO `auth_user` VALUES (1,'pbkdf2_sha256$870000$rOMsfXA8M6F13VsrCfukdJ$s/PPiQIGZ23pwkzDb0s5C0hHK4FX5xvUU8uIgtwGcTU=','2025-07-15 06:06:35.688068',1,'admin','Demetri','Manias','demetrimanias@gmail.com',1,1,'2025-01-19 06:36:42.906568'),(2,'pbkdf2_sha256$870000$DzTTMWgzeI9Iw00hqD6yh8$ef7k4XbVx+uard2uHCf7VSunRhkv7uzPN4ux5UKRdNQ=',NULL,1,'Demetrios','Demetrios','Manias','demetri.manias@alivente.com',1,1,'2025-01-23 17:15:24.000000'),(3,'pbkdf2_sha256$870000$g4JLFQKB5C1PrvRP47Yy2X$doEkZ7Ebt+SkBLb4lxgOaBcgVCTcOxjFXEwHxEyM5P0=','2025-02-04 13:19:57.000000',1,'angy','Angela','Manias','angmaniasbakers@gmail.com',1,1,'2025-02-04 05:55:15.000000'),(5,'pbkdf2_sha256$870000$27FnwEnVd0hzuWGuoxust6$YT0Xy0bGQAAuArQZWH9VMFd0CFhkvFmJ8gM9mpao42c=','2025-06-30 13:27:18.131849',0,'StellaSimi','Stella','Simitopoulos','stella.simitopoulos@alivente.com',0,1,'2025-02-05 09:19:49.000000');
/*!40000 ALTER TABLE `auth_user` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `auth_user_groups`
--

DROP TABLE IF EXISTS `auth_user_groups`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `auth_user_groups` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `group_id` int NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `auth_user_groups_user_id_group_id_94350c0c_uniq` (`user_id`,`group_id`),
  KEY `auth_user_groups_group_id_97559544_fk_auth_group_id` (`group_id`),
  CONSTRAINT `auth_user_groups_group_id_97559544_fk_auth_group_id` FOREIGN KEY (`group_id`) REFERENCES `auth_group` (`id`),
  CONSTRAINT `auth_user_groups_user_id_6a12ed8b_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `auth_user_groups`
--

LOCK TABLES `auth_user_groups` WRITE;
/*!40000 ALTER TABLE `auth_user_groups` DISABLE KEYS */;
/*!40000 ALTER TABLE `auth_user_groups` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `auth_user_user_permissions`
--

DROP TABLE IF EXISTS `auth_user_user_permissions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `auth_user_user_permissions` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `permission_id` int NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `auth_user_user_permissions_user_id_permission_id_14a6b632_uniq` (`user_id`,`permission_id`),
  KEY `auth_user_user_permi_permission_id_1fbb5f2c_fk_auth_perm` (`permission_id`),
  CONSTRAINT `auth_user_user_permi_permission_id_1fbb5f2c_fk_auth_perm` FOREIGN KEY (`permission_id`) REFERENCES `auth_permission` (`id`),
  CONSTRAINT `auth_user_user_permissions_user_id_a95ead1b_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=125 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `auth_user_user_permissions`
--

LOCK TABLES `auth_user_user_permissions` WRITE;
/*!40000 ALTER TABLE `auth_user_user_permissions` DISABLE KEYS */;
INSERT INTO `auth_user_user_permissions` VALUES (1,2,1),(2,2,2),(3,2,3),(4,2,4),(5,2,5),(6,2,6),(7,2,7),(8,2,8),(9,2,9),(10,2,10),(11,2,11),(12,2,12),(13,2,13),(14,2,14),(15,2,15),(16,2,16),(17,2,17),(18,2,18),(19,2,19),(20,2,20),(21,2,21),(22,2,22),(23,2,23),(24,2,24),(25,2,25),(26,2,26),(27,2,27),(28,2,28),(29,2,29),(30,2,30),(31,2,31),(32,2,32),(33,2,33),(34,2,34),(35,2,35),(36,2,36),(37,2,37),(38,2,38),(39,2,39),(40,2,40),(41,2,41),(42,2,42),(43,2,43),(44,2,44),(45,2,45),(46,2,46),(47,2,47),(48,2,48),(49,2,49),(50,2,50),(51,2,51),(52,2,52),(53,3,17),(54,3,18),(55,3,19),(56,3,20),(57,3,21),(58,3,22),(59,3,23),(60,3,24),(61,3,25),(62,3,26),(63,3,27),(64,3,28),(65,3,29),(66,3,30),(67,3,31),(68,3,32),(69,3,33),(70,3,34),(71,3,35),(72,3,36),(73,3,37),(74,3,38),(75,3,39),(76,3,40),(77,3,41),(78,3,42),(79,3,43),(80,3,44),(81,3,45),(82,3,46),(83,3,47),(84,3,48),(85,3,49),(86,3,50),(87,3,51),(88,3,52),(89,3,53),(90,3,54),(91,3,55),(92,3,56),(93,5,25),(94,5,26),(95,5,27),(96,5,28),(97,5,29),(98,5,30),(99,5,31),(100,5,32),(101,5,33),(102,5,34),(103,5,35),(104,5,36),(105,5,37),(106,5,38),(107,5,39),(108,5,40),(109,5,41),(110,5,42),(111,5,43),(112,5,44),(113,5,45),(114,5,46),(115,5,47),(116,5,48),(117,5,49),(118,5,50),(119,5,51),(120,5,52),(121,5,53),(122,5,54),(123,5,55),(124,5,56);
/*!40000 ALTER TABLE `auth_user_user_permissions` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `django_admin_log`
--

DROP TABLE IF EXISTS `django_admin_log`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `django_admin_log` (
  `id` int NOT NULL AUTO_INCREMENT,
  `action_time` datetime(6) NOT NULL,
  `object_id` longtext,
  `object_repr` varchar(200) NOT NULL,
  `action_flag` smallint unsigned NOT NULL,
  `change_message` longtext NOT NULL,
  `content_type_id` int DEFAULT NULL,
  `user_id` int NOT NULL,
  PRIMARY KEY (`id`),
  KEY `django_admin_log_content_type_id_c4bce8eb_fk_django_co` (`content_type_id`),
  KEY `django_admin_log_user_id_c564eba6_fk_auth_user_id` (`user_id`),
  CONSTRAINT `django_admin_log_content_type_id_c4bce8eb_fk_django_co` FOREIGN KEY (`content_type_id`) REFERENCES `django_content_type` (`id`),
  CONSTRAINT `django_admin_log_user_id_c564eba6_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`),
  CONSTRAINT `django_admin_log_chk_1` CHECK ((`action_flag` >= 0))
) ENGINE=InnoDB AUTO_INCREMENT=17 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `django_admin_log`
--

LOCK TABLES `django_admin_log` WRITE;
/*!40000 ALTER TABLE `django_admin_log` DISABLE KEYS */;
INSERT INTO `django_admin_log` VALUES (1,'2025-01-23 17:15:24.439073','2','Demetrios',1,'[{\"added\": {}}]',4,1),(2,'2025-01-23 17:16:13.214982','2','Demetrios',2,'[{\"changed\": {\"fields\": [\"First name\", \"Last name\", \"Email address\", \"Superuser status\", \"User permissions\"]}}]',4,1),(3,'2025-01-23 17:16:30.596951','2','Demetrios',2,'[{\"changed\": {\"fields\": [\"Staff status\"]}}]',4,1),(4,'2025-02-04 05:55:16.230313','3','angy',1,'[{\"added\": {}}]',4,1),(5,'2025-02-04 05:57:44.762520','3','angy',2,'[{\"changed\": {\"fields\": [\"First name\", \"Last name\", \"Email address\", \"User permissions\"]}}]',4,1),(6,'2025-02-04 07:21:16.128272','1','every 7 days',1,'[{\"added\": {}}]',16,1),(7,'2025-02-04 07:21:32.278361','1','every 7 days',3,'',16,1),(8,'2025-02-04 07:24:47.157055','2','every day',1,'[{\"added\": {}}]',16,1),(9,'2025-02-04 07:46:25.879836','1','Test - Demetri: every day',1,'[{\"added\": {}}]',17,1),(13,'2025-02-05 09:19:49.834909','5','StellaSimi',1,'[{\"added\": {}}]',4,1),(14,'2025-02-05 09:22:02.957023','5','StellaSimi',2,'[{\"changed\": {\"fields\": [\"First name\", \"Last name\", \"Email address\", \"User permissions\"]}}]',4,1),(15,'2025-05-30 07:34:26.941800','3','angy',2,'[{\"changed\": {\"fields\": [\"Superuser status\"]}}]',4,1),(16,'2025-05-30 07:34:51.903196','3','angy',2,'[{\"changed\": {\"fields\": [\"Staff status\"]}}]',4,1);
/*!40000 ALTER TABLE `django_admin_log` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `django_celery_beat_clockedschedule`
--

DROP TABLE IF EXISTS `django_celery_beat_clockedschedule`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `django_celery_beat_clockedschedule` (
  `id` int NOT NULL AUTO_INCREMENT,
  `clocked_time` datetime(6) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `django_celery_beat_clockedschedule`
--

LOCK TABLES `django_celery_beat_clockedschedule` WRITE;
/*!40000 ALTER TABLE `django_celery_beat_clockedschedule` DISABLE KEYS */;
/*!40000 ALTER TABLE `django_celery_beat_clockedschedule` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `django_celery_beat_crontabschedule`
--

DROP TABLE IF EXISTS `django_celery_beat_crontabschedule`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `django_celery_beat_crontabschedule` (
  `id` int NOT NULL AUTO_INCREMENT,
  `minute` varchar(240) NOT NULL,
  `hour` varchar(96) NOT NULL,
  `day_of_week` varchar(64) NOT NULL,
  `day_of_month` varchar(124) NOT NULL,
  `month_of_year` varchar(64) NOT NULL,
  `timezone` varchar(63) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `django_celery_beat_crontabschedule`
--

LOCK TABLES `django_celery_beat_crontabschedule` WRITE;
/*!40000 ALTER TABLE `django_celery_beat_crontabschedule` DISABLE KEYS */;
/*!40000 ALTER TABLE `django_celery_beat_crontabschedule` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `django_celery_beat_intervalschedule`
--

DROP TABLE IF EXISTS `django_celery_beat_intervalschedule`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `django_celery_beat_intervalschedule` (
  `id` int NOT NULL AUTO_INCREMENT,
  `every` int NOT NULL,
  `period` varchar(24) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `django_celery_beat_intervalschedule`
--

LOCK TABLES `django_celery_beat_intervalschedule` WRITE;
/*!40000 ALTER TABLE `django_celery_beat_intervalschedule` DISABLE KEYS */;
INSERT INTO `django_celery_beat_intervalschedule` VALUES (2,1,'days');
/*!40000 ALTER TABLE `django_celery_beat_intervalschedule` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `django_celery_beat_periodictask`
--

DROP TABLE IF EXISTS `django_celery_beat_periodictask`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `django_celery_beat_periodictask` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(200) NOT NULL,
  `task` varchar(200) NOT NULL,
  `args` longtext NOT NULL,
  `kwargs` longtext NOT NULL,
  `queue` varchar(200) DEFAULT NULL,
  `exchange` varchar(200) DEFAULT NULL,
  `routing_key` varchar(200) DEFAULT NULL,
  `expires` datetime(6) DEFAULT NULL,
  `enabled` tinyint(1) NOT NULL,
  `last_run_at` datetime(6) DEFAULT NULL,
  `total_run_count` int unsigned NOT NULL,
  `date_changed` datetime(6) NOT NULL,
  `description` longtext NOT NULL,
  `crontab_id` int DEFAULT NULL,
  `interval_id` int DEFAULT NULL,
  `solar_id` int DEFAULT NULL,
  `one_off` tinyint(1) NOT NULL,
  `start_time` datetime(6) DEFAULT NULL,
  `priority` int unsigned DEFAULT NULL,
  `headers` longtext NOT NULL DEFAULT (_utf8mb3'{}'),
  `clocked_id` int DEFAULT NULL,
  `expire_seconds` int unsigned DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`),
  KEY `django_celery_beat_p_crontab_id_d3cba168_fk_django_ce` (`crontab_id`),
  KEY `django_celery_beat_p_interval_id_a8ca27da_fk_django_ce` (`interval_id`),
  KEY `django_celery_beat_p_solar_id_a87ce72c_fk_django_ce` (`solar_id`),
  KEY `django_celery_beat_p_clocked_id_47a69f82_fk_django_ce` (`clocked_id`),
  CONSTRAINT `django_celery_beat_p_clocked_id_47a69f82_fk_django_ce` FOREIGN KEY (`clocked_id`) REFERENCES `django_celery_beat_clockedschedule` (`id`),
  CONSTRAINT `django_celery_beat_p_crontab_id_d3cba168_fk_django_ce` FOREIGN KEY (`crontab_id`) REFERENCES `django_celery_beat_crontabschedule` (`id`),
  CONSTRAINT `django_celery_beat_p_interval_id_a8ca27da_fk_django_ce` FOREIGN KEY (`interval_id`) REFERENCES `django_celery_beat_intervalschedule` (`id`),
  CONSTRAINT `django_celery_beat_p_solar_id_a87ce72c_fk_django_ce` FOREIGN KEY (`solar_id`) REFERENCES `django_celery_beat_solarschedule` (`id`),
  CONSTRAINT `django_celery_beat_periodictask_chk_1` CHECK ((`total_run_count` >= 0)),
  CONSTRAINT `django_celery_beat_periodictask_chk_2` CHECK ((`priority` >= 0)),
  CONSTRAINT `django_celery_beat_periodictask_chk_3` CHECK ((`expire_seconds` >= 0))
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `django_celery_beat_periodictask`
--

LOCK TABLES `django_celery_beat_periodictask` WRITE;
/*!40000 ALTER TABLE `django_celery_beat_periodictask` DISABLE KEYS */;
INSERT INTO `django_celery_beat_periodictask` VALUES (1,'Test - Demetri','open_invoices.py','[]','{}',NULL,NULL,NULL,NULL,1,NULL,0,'2025-02-04 07:46:25.877823','Demetri Test - Scheduled Task',NULL,2,NULL,0,'2025-02-04 07:25:03.000000',NULL,'{}',NULL,NULL);
/*!40000 ALTER TABLE `django_celery_beat_periodictask` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `django_celery_beat_periodictasks`
--

DROP TABLE IF EXISTS `django_celery_beat_periodictasks`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `django_celery_beat_periodictasks` (
  `ident` smallint NOT NULL,
  `last_update` datetime(6) NOT NULL,
  PRIMARY KEY (`ident`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `django_celery_beat_periodictasks`
--

LOCK TABLES `django_celery_beat_periodictasks` WRITE;
/*!40000 ALTER TABLE `django_celery_beat_periodictasks` DISABLE KEYS */;
INSERT INTO `django_celery_beat_periodictasks` VALUES (1,'2025-02-04 07:46:25.878822');
/*!40000 ALTER TABLE `django_celery_beat_periodictasks` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `django_celery_beat_solarschedule`
--

DROP TABLE IF EXISTS `django_celery_beat_solarschedule`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `django_celery_beat_solarschedule` (
  `id` int NOT NULL AUTO_INCREMENT,
  `event` varchar(24) NOT NULL,
  `latitude` decimal(9,6) NOT NULL,
  `longitude` decimal(9,6) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `django_celery_beat_solar_event_latitude_longitude_ba64999a_uniq` (`event`,`latitude`,`longitude`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `django_celery_beat_solarschedule`
--

LOCK TABLES `django_celery_beat_solarschedule` WRITE;
/*!40000 ALTER TABLE `django_celery_beat_solarschedule` DISABLE KEYS */;
/*!40000 ALTER TABLE `django_celery_beat_solarschedule` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `django_content_type`
--

DROP TABLE IF EXISTS `django_content_type`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `django_content_type` (
  `id` int NOT NULL AUTO_INCREMENT,
  `app_label` varchar(100) NOT NULL,
  `model` varchar(100) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `django_content_type_app_label_model_76bd3d3b_uniq` (`app_label`,`model`)
) ENGINE=InnoDB AUTO_INCREMENT=29 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `django_content_type`
--

LOCK TABLES `django_content_type` WRITE;
/*!40000 ALTER TABLE `django_content_type` DISABLE KEYS */;
INSERT INTO `django_content_type` VALUES (1,'admin','logentry'),(3,'auth','group'),(2,'auth','permission'),(4,'auth','user'),(5,'contenttypes','contenttype'),(20,'django_celery_beat','clockedschedule'),(15,'django_celery_beat','crontabschedule'),(16,'django_celery_beat','intervalschedule'),(17,'django_celery_beat','periodictask'),(18,'django_celery_beat','periodictasks'),(19,'django_celery_beat','solarschedule'),(28,'pages','act_expense'),(27,'pages','expense'),(25,'pages','expense_line_types'),(26,'pages','expense_types'),(10,'pages','invoices'),(11,'pages','issues'),(12,'pages','issues_details'),(9,'pages','petty'),(21,'pages','prop_values'),(7,'pages','properties'),(8,'pages','props'),(22,'pages','revenue'),(23,'pages','revenue_line_types'),(24,'pages','revenue_types'),(14,'pages','supplier'),(13,'pages','tenant'),(6,'sessions','session');
/*!40000 ALTER TABLE `django_content_type` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `django_migrations`
--

DROP TABLE IF EXISTS `django_migrations`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `django_migrations` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `app` varchar(255) NOT NULL,
  `name` varchar(255) NOT NULL,
  `applied` datetime(6) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=170 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `django_migrations`
--

LOCK TABLES `django_migrations` WRITE;
/*!40000 ALTER TABLE `django_migrations` DISABLE KEYS */;
INSERT INTO `django_migrations` VALUES (1,'contenttypes','0001_initial','2025-01-19 06:32:34.864693'),(2,'auth','0001_initial','2025-01-19 06:32:35.149246'),(3,'admin','0001_initial','2025-01-19 06:32:35.222963'),(4,'admin','0002_logentry_remove_auto_add','2025-01-19 06:32:35.228617'),(5,'admin','0003_logentry_add_action_flag_choices','2025-01-19 06:32:35.234381'),(6,'contenttypes','0002_remove_content_type_name','2025-01-19 06:32:35.295527'),(7,'auth','0002_alter_permission_name_max_length','2025-01-19 06:32:35.332185'),(8,'auth','0003_alter_user_email_max_length','2025-01-19 06:32:35.348109'),(9,'auth','0004_alter_user_username_opts','2025-01-19 06:32:35.352807'),(10,'auth','0005_alter_user_last_login_null','2025-01-19 06:32:35.392071'),(11,'auth','0006_require_contenttypes_0002','2025-01-19 06:32:35.394015'),(12,'auth','0007_alter_validators_add_error_messages','2025-01-19 06:32:35.398888'),(13,'auth','0008_alter_user_username_max_length','2025-01-19 06:32:35.429602'),(14,'auth','0009_alter_user_last_name_max_length','2025-01-19 06:32:35.466743'),(15,'auth','0010_alter_group_name_max_length','2025-01-19 06:32:35.480344'),(16,'auth','0011_update_proxy_permissions','2025-01-19 06:32:35.485153'),(17,'auth','0012_alter_user_first_name_max_length','2025-01-19 06:32:35.519665'),(18,'sessions','0001_initial','2025-01-19 06:32:35.544415'),(127,'pages','0001_initial','2025-01-24 05:24:47.326729'),(128,'pages','0002_alter_tenant_tenant_deposit_and_more','2025-01-27 13:00:19.371898'),(129,'pages','0003_alter_tenant_tenant_deposit_and_more','2025-01-28 11:41:34.196705'),(133,'pages','0004_supplier','2025-02-03 03:34:55.056187'),(134,'pages','0005_supplier_supplier_country','2025-02-03 03:34:55.066921'),(135,'pages','0006_delete_supplier','2025-02-03 03:34:55.074421'),(136,'pages','0007_supplier','2025-02-03 03:34:55.091026'),(137,'django_celery_beat','0001_initial','2025-02-04 07:12:34.036624'),(138,'django_celery_beat','0002_auto_20161118_0346','2025-02-04 07:12:34.086268'),(139,'django_celery_beat','0003_auto_20161209_0049','2025-02-04 07:12:34.103012'),(140,'django_celery_beat','0004_auto_20170221_0000','2025-02-04 07:12:34.107023'),(141,'django_celery_beat','0005_add_solarschedule_events_choices','2025-02-04 07:12:34.110637'),(142,'django_celery_beat','0006_auto_20180322_0932','2025-02-04 07:12:34.186824'),(143,'django_celery_beat','0007_auto_20180521_0826','2025-02-04 07:12:34.244160'),(144,'django_celery_beat','0008_auto_20180914_1922','2025-02-04 07:12:34.268565'),(145,'django_celery_beat','0006_auto_20180210_1226','2025-02-04 07:12:34.284823'),(146,'django_celery_beat','0006_periodictask_priority','2025-02-04 07:12:34.332205'),(147,'django_celery_beat','0009_periodictask_headers','2025-02-04 07:12:34.374038'),(148,'django_celery_beat','0010_auto_20190429_0326','2025-02-04 07:12:34.537277'),(149,'django_celery_beat','0011_auto_20190508_0153','2025-02-04 07:12:34.605997'),(150,'django_celery_beat','0012_periodictask_expire_seconds','2025-02-04 07:12:34.658673'),(151,'django_celery_beat','0013_auto_20200609_0727','2025-02-04 07:12:34.669943'),(152,'django_celery_beat','0014_remove_clockedschedule_enabled','2025-02-04 07:12:34.687966'),(153,'django_celery_beat','0015_edit_solarschedule_events_choices','2025-02-04 07:12:34.692080'),(154,'django_celery_beat','0016_alter_crontabschedule_timezone','2025-02-04 07:12:34.701172'),(155,'django_celery_beat','0017_alter_crontabschedule_month_of_year','2025-02-04 07:12:34.708251'),(156,'django_celery_beat','0018_improve_crontab_helptext','2025-02-04 07:12:34.716609'),(157,'django_celery_beat','0019_alter_periodictasks_options','2025-02-04 07:12:34.719500'),(158,'pages','0008_alter_petty_petty_cash_description','2025-02-04 08:53:05.009469'),(159,'pages','0009_prop_values','2025-05-10 18:15:13.684683'),(160,'pages','0010_revenue_line_types_revenue_types_revenue','2025-05-12 16:23:38.561262'),(161,'pages','0011_expense_line_types_expense_types_expense','2025-05-13 04:32:30.172036'),(162,'pages','0012_act_expense','2025-05-25 13:16:03.739053'),(163,'pages','0013_act_expense_act_expense_document','2025-06-02 15:39:00.457434'),(164,'pages','0014_alter_act_expense_act_expense_document','2025-06-03 04:21:22.180322'),(165,'pages','0015_alter_props_prop_title_deed','2025-06-03 12:10:59.515661'),(166,'pages','0016_alter_props_options','2025-06-03 12:12:12.912783'),(167,'pages','0017_alter_tenant_options_and_more','2025-06-04 03:48:33.940610'),(168,'pages','0018_props_prop_latitude_props_prop_longitude','2025-06-12 09:19:29.459501'),(169,'pages','0019_tenant_tenant_renewal_status','2025-06-25 04:10:10.178150');
/*!40000 ALTER TABLE `django_migrations` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `django_session`
--

DROP TABLE IF EXISTS `django_session`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `django_session` (
  `session_key` varchar(40) NOT NULL,
  `session_data` longtext NOT NULL,
  `expire_date` datetime(6) NOT NULL,
  PRIMARY KEY (`session_key`),
  KEY `django_session_expire_date_a5c62663` (`expire_date`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `django_session`
--

LOCK TABLES `django_session` WRITE;
/*!40000 ALTER TABLE `django_session` DISABLE KEYS */;
INSERT INTO `django_session` VALUES ('0kt0u35aqdgbnhaalpdom6v13zdvis9d','.eJxVjDsOwjAQRO_iGlnrT_yhpM8ZrLXXxgHkSHFSIe5OIqWAcua9mTcLuK01bD0vYSJ2ZYJdfruI6ZnbAeiB7T7zNLd1mSI_FH7SzseZ8ut2un8HFXvd16BKpmIsAaQiySWninJKkIU9Dug1qcFjFERZkUANRoME7ayXZGJmny_zzTf4:1u5394:U_z1NiOLK35zpSbbGaXUeP0VPMu1_flLfWuu9wB-D28','2025-04-30 13:49:42.004961'),('1lzd71pgyw6pphngd3ujv2xehpx8tnp4','.eJxVjckOgyAURf-FdUMQHNBl9_0G8uQ9qq2IAUw6pP9eTVy0yzud-2YG1jyYNVE0I7KOFez06_Vg7zTvAd5gvgZuw5zj2PO9wo808UtAms5H9w8wQBq2tVCO0NUNCmGdRG21ckqrAhuxyQraElXVQl8gksICSlGXQopSN63EuqcNOkHKJtISYjb5udBGTav3EMcX7aceHsYG72nOiXXy8wVrh0ne:1uWFMY:eYA_WMzApaAfHCp4leylpMYxPRllKRqYUDS5Olp7CUc','2025-07-14 14:20:02.676233'),('4e0y1itxvv3g0hu8ttcrxk1zdiryomzw','.eJxVjDsOwjAQRO_iGlnrT_yhpM8ZrLXXxgHkSHFSIe5OIqWAcua9mTcLuK01bD0vYSJ2ZYJdfruI6ZnbAeiB7T7zNLd1mSI_FH7SzseZ8ut2un8HFXvd16BKpmIsAaQiySWninJKkIU9Dug1qcFjFERZkUANRoME7ayXZGJmny_zzTf4:1tfbWy:OJECQerqUgsxVc72nhr1p_EYzJz8blUr8ocN3KZFevo','2025-02-19 09:17:12.435157'),('kvxcss2pd6118a0lly75beu6rfmmqbag','.eJxVjDsOwjAQRO_iGlnrT_yhpM8ZrLXXxgHkSHFSIe5OIqWAcua9mTcLuK01bD0vYSJ2ZYJdfruI6ZnbAeiB7T7zNLd1mSI_FH7SzseZ8ut2un8HFXvd16BKpmIsAaQiySWninJKkIU9Dug1qcFjFERZkUANRoME7ayXZGJmny_zzTf4:1uRRfT:IfQx6JauMxQ8i1yoYkPkIAz7SrluhSdBslxhsg-BrVE','2025-07-01 08:27:43.816706'),('osfn44msflqn07vbtovtqm5spnw556an','.eJxVjDsOwjAQRO_iGlnrT_yhpM8ZrLXXxgHkSHFSIe5OIqWAcua9mTcLuK01bD0vYSJ2ZYJdfruI6ZnbAeiB7T7zNLd1mSI_FH7SzseZ8ut2un8HFXvd16BKpmIsAaQiySWninJKkIU9Dug1qcFjFERZkUANRoME7ayXZGJmny_zzTf4:1uMiC0:aeeeiWZ3A-QaeCZAkB37b2JqjPU9Vt3-OxJtqIrsyd0','2025-06-18 07:05:44.452576'),('xq73kgf61h91sxxnamssoy63m04n69ax','.eJxVjsEOwiAQRP-FsyFLoS316N1vIAu72GpTGqAHY_x328SDHmfmzWRewuFWR7cVzm4icRZKnH49j-HByxHQHZdbkiEtNU9eHoj8pkVeE_F8-bJ_AyOWcW-Djkyx6wkgxIZssDpqqxX1sMsWB0O6HdArItak0EBnoAFj-6GhzvM-OmOpLvOacnX1ufLxiStOM5N4fwArS0Ly:1uba0v:-FC5weOFAxYpl8s9l0bDI7_K7MALbcCaIjAgpvUioAc','2025-07-29 07:23:45.533287');
/*!40000 ALTER TABLE `django_session` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `expense`
--

DROP TABLE IF EXISTS `expense`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `expense` (
  `expense_id` int NOT NULL AUTO_INCREMENT,
  `expense_amount` decimal(8,2) DEFAULT NULL,
  `expense_jan` decimal(8,2) DEFAULT NULL,
  `expense_feb` decimal(8,2) DEFAULT NULL,
  `expense_mar` decimal(8,2) DEFAULT NULL,
  `expense_apr` decimal(8,2) DEFAULT NULL,
  `expense_may` decimal(8,2) DEFAULT NULL,
  `expense_jun` decimal(8,2) DEFAULT NULL,
  `expense_jul` decimal(8,2) DEFAULT NULL,
  `expense_aug` decimal(8,2) DEFAULT NULL,
  `expense_sep` decimal(8,2) DEFAULT NULL,
  `expense_oct` decimal(8,2) DEFAULT NULL,
  `expense_nov` decimal(8,2) DEFAULT NULL,
  `expense_dec` decimal(8,2) DEFAULT NULL,
  `prop_id` int NOT NULL,
  `expense_line_types_id` int NOT NULL,
  `expense_types_id` int NOT NULL,
  PRIMARY KEY (`expense_id`),
  KEY `expense_prop_id_8baf8647_fk_prop_prop_id` (`prop_id`),
  KEY `expense_expense_line_types_i_621e6596_fk_expense_l` (`expense_line_types_id`),
  KEY `expense_expense_types_id_ae9558af_fk_expense_t` (`expense_types_id`),
  CONSTRAINT `expense_expense_line_types_i_621e6596_fk_expense_l` FOREIGN KEY (`expense_line_types_id`) REFERENCES `expense_line_types` (`expense_line_types_id`),
  CONSTRAINT `expense_expense_types_id_ae9558af_fk_expense_t` FOREIGN KEY (`expense_types_id`) REFERENCES `expense_types` (`expense_types_id`),
  CONSTRAINT `expense_prop_id_8baf8647_fk_prop_prop_id` FOREIGN KEY (`prop_id`) REFERENCES `prop` (`prop_id`)
) ENGINE=InnoDB AUTO_INCREMENT=172 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `expense`
--

LOCK TABLES `expense` WRITE;
/*!40000 ALTER TABLE `expense` DISABLE KEYS */;
INSERT INTO `expense` VALUES (1,159.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,159.00,0.00,0.00,1,1,15),(5,24.77,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,24.77,0.00,1,4,16),(6,280.00,280.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,1,5,6),(7,180.00,0.00,0.00,0.00,0.00,0.00,0.00,180.00,0.00,0.00,0.00,0.00,0.00,1,6,12),(8,277.56,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,277.56,0.00,0.00,0.00,1,7,14),(28,474.58,NULL,NULL,NULL,NULL,NULL,474.58,NULL,NULL,NULL,NULL,NULL,NULL,5,8,11),(29,711.86,NULL,NULL,NULL,NULL,NULL,711.86,NULL,NULL,NULL,NULL,NULL,NULL,4,8,11),(30,474.58,NULL,NULL,NULL,NULL,NULL,474.58,NULL,NULL,NULL,NULL,NULL,NULL,2,8,11),(31,1067.80,NULL,NULL,NULL,NULL,NULL,1067.80,NULL,NULL,NULL,NULL,NULL,NULL,7,8,11),(32,474.58,NULL,NULL,NULL,NULL,NULL,474.58,NULL,NULL,NULL,NULL,NULL,NULL,1,8,11),(33,949.15,NULL,NULL,NULL,NULL,NULL,949.15,NULL,NULL,NULL,NULL,NULL,NULL,3,8,11),(34,569.49,NULL,NULL,NULL,NULL,NULL,569.49,NULL,NULL,NULL,NULL,NULL,NULL,9,8,11),(35,664.41,NULL,NULL,NULL,NULL,NULL,664.41,NULL,NULL,NULL,NULL,NULL,NULL,10,8,11),(36,664.41,NULL,NULL,NULL,NULL,NULL,664.41,NULL,NULL,NULL,NULL,NULL,NULL,11,8,11),(37,949.15,NULL,NULL,NULL,NULL,NULL,949.15,NULL,NULL,NULL,NULL,NULL,NULL,12,8,11),(58,375.60,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,375.60,NULL,NULL,NULL,3,7,14),(59,270.00,270.00,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,3,5,6),(60,270.00,NULL,NULL,NULL,NULL,NULL,NULL,270.00,NULL,NULL,NULL,NULL,NULL,3,6,12),(61,46.93,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,46.93,NULL,3,4,16),(63,187.00,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0.00,187.00,NULL,NULL,3,1,15),(64,500.00,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0.00,500.00,NULL,NULL,7,1,15),(66,50.00,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,50.00,NULL,7,4,16),(67,1200.00,1200.00,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,7,5,6),(68,372.76,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,372.76,NULL,NULL,NULL,7,7,14),(69,400.00,NULL,NULL,NULL,NULL,NULL,400.00,NULL,400.00,NULL,400.00,NULL,NULL,7,21,4),(70,160.00,NULL,NULL,NULL,NULL,NULL,160.00,NULL,160.00,NULL,160.00,NULL,NULL,7,22,4),(71,555.00,NULL,NULL,NULL,NULL,555.00,555.00,555.00,555.00,555.00,555.00,NULL,NULL,7,23,3),(72,72.00,72.00,72.00,72.00,72.00,72.00,72.00,72.00,72.00,72.00,72.00,72.00,72.00,7,24,1),(73,40.00,40.00,40.00,40.00,40.00,40.00,40.00,40.00,40.00,40.00,40.00,40.00,40.00,7,25,1),(74,375.00,375.00,NULL,NULL,375.00,NULL,NULL,375.00,NULL,NULL,375.00,NULL,NULL,7,26,2),(75,185.00,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0.00,185.00,NULL,NULL,4,1,15),(77,25.00,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,25.00,NULL,4,4,16),(78,245.00,245.00,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,4,5,6),(79,210.00,NULL,NULL,NULL,NULL,NULL,NULL,210.00,NULL,NULL,NULL,NULL,NULL,4,6,12),(80,362.00,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,362.00,NULL,NULL,NULL,4,7,14),(81,187.00,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0.00,187.00,NULL,NULL,2,1,15),(83,210.00,210.00,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,2,5,6),(84,180.00,NULL,NULL,NULL,NULL,NULL,NULL,180.00,NULL,NULL,NULL,NULL,NULL,2,6,12),(85,282.32,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,282.32,NULL,NULL,NULL,2,7,14),(86,25.00,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,25.00,NULL,2,4,16),(87,185.00,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,185.00,NULL,NULL,5,1,15),(89,25.00,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,25.00,NULL,5,4,16),(90,180.00,180.00,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,5,5,6),(91,180.00,NULL,NULL,NULL,NULL,NULL,NULL,180.00,NULL,NULL,NULL,NULL,NULL,5,6,12),(92,282.32,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,282.32,NULL,NULL,NULL,5,7,14),(93,214.30,214.30,214.30,214.30,214.30,214.30,214.30,214.30,214.30,214.30,214.30,214.30,214.30,9,28,1),(94,250.02,250.02,250.02,250.02,250.02,250.02,250.02,250.02,250.02,250.02,250.02,250.02,250.02,10,28,1),(95,250.02,250.02,250.02,250.02,250.02,250.02,250.02,250.02,250.02,250.02,250.02,250.02,250.02,11,28,1),(96,214.04,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,214.04,NULL,NULL,NULL,9,29,14),(97,249.71,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,249.71,NULL,NULL,NULL,10,29,14),(98,249.71,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,249.71,NULL,NULL,NULL,11,29,14),(99,744.00,NULL,NULL,NULL,NULL,NULL,NULL,NULL,744.00,NULL,NULL,NULL,NULL,9,17,13),(100,868.00,NULL,NULL,NULL,NULL,NULL,NULL,NULL,868.00,NULL,NULL,NULL,NULL,10,17,13),(101,868.00,NULL,NULL,NULL,NULL,NULL,NULL,NULL,868.00,NULL,NULL,NULL,NULL,11,17,13),(102,262.79,262.79,NULL,NULL,262.79,NULL,NULL,262.79,NULL,NULL,262.79,NULL,NULL,12,5,2),(103,62.00,62.00,62.00,62.00,62.00,62.00,62.00,62.00,62.00,62.00,62.00,62.00,62.00,12,16,1),(104,257.83,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,257.83,NULL,NULL,NULL,12,30,14),(105,150.00,150.00,NULL,NULL,150.00,NULL,NULL,150.00,NULL,NULL,150.00,NULL,NULL,12,18,2),(152,32.63,32.63,32.63,32.63,32.63,32.63,32.63,32.63,32.63,32.63,32.63,32.63,32.63,5,9,1),(153,52.20,52.20,52.20,52.20,52.20,52.20,52.20,52.20,52.20,52.20,52.20,52.20,52.20,4,9,1),(154,32.63,32.63,32.63,32.63,32.63,32.63,32.63,32.63,32.63,32.63,32.63,32.63,32.63,2,9,1),(155,73.41,73.41,73.41,73.41,73.41,73.41,73.41,73.41,73.41,73.41,73.41,73.41,73.41,7,9,1),(156,32.63,32.63,32.63,32.63,32.63,32.63,32.63,32.63,32.63,32.63,32.63,32.63,32.63,1,9,1),(157,69.33,69.33,69.33,69.33,69.33,69.33,69.33,69.33,69.33,69.33,69.33,69.33,69.33,3,9,1),(158,40.78,40.78,40.78,40.78,40.78,40.78,40.78,40.78,40.78,40.78,40.78,40.78,40.78,9,9,1),(159,48.94,48.94,48.94,48.94,48.94,48.94,48.94,48.94,48.94,48.94,48.94,48.94,48.94,10,9,1),(160,48.94,48.94,48.94,48.94,48.94,48.94,48.94,48.94,48.94,48.94,48.94,48.94,48.94,11,9,1),(161,68.52,68.52,68.52,68.52,68.52,68.52,68.52,68.52,68.52,68.52,68.52,68.52,68.52,12,9,1),(162,183.36,NULL,NULL,NULL,NULL,NULL,183.36,NULL,NULL,NULL,NULL,NULL,NULL,5,3,11),(163,293.38,NULL,NULL,NULL,NULL,NULL,293.38,NULL,NULL,NULL,NULL,NULL,NULL,4,3,11),(164,183.36,NULL,NULL,NULL,NULL,NULL,183.36,NULL,NULL,NULL,NULL,NULL,NULL,2,3,11),(165,412.56,NULL,NULL,NULL,NULL,NULL,412.56,NULL,NULL,NULL,NULL,NULL,NULL,7,3,11),(166,183.36,NULL,NULL,NULL,NULL,NULL,183.36,NULL,NULL,NULL,NULL,NULL,NULL,1,3,11),(167,389.64,NULL,NULL,NULL,NULL,NULL,389.64,NULL,NULL,NULL,NULL,NULL,NULL,3,3,11),(168,229.20,NULL,NULL,NULL,NULL,NULL,229.20,NULL,NULL,NULL,NULL,NULL,NULL,9,3,11),(169,275.04,NULL,NULL,NULL,NULL,NULL,275.04,NULL,NULL,NULL,NULL,NULL,NULL,10,3,11),(170,275.04,NULL,NULL,NULL,NULL,NULL,275.04,NULL,NULL,NULL,NULL,NULL,NULL,11,3,11),(171,385.06,NULL,NULL,NULL,NULL,NULL,385.06,NULL,NULL,NULL,NULL,NULL,NULL,12,3,11);
/*!40000 ALTER TABLE `expense` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `expense_line_types`
--

DROP TABLE IF EXISTS `expense_line_types`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `expense_line_types` (
  `expense_line_types_id` int NOT NULL AUTO_INCREMENT,
  `expense_line_types_name` varchar(255) DEFAULT NULL,
  `expense_line_types_description` varchar(255) DEFAULT NULL,
  `expense_line_types_prorata` varchar(3) DEFAULT NULL,
  `expense_line_types_pr_amount` decimal(8,2) DEFAULT NULL,
  PRIMARY KEY (`expense_line_types_id`)
) ENGINE=InnoDB AUTO_INCREMENT=31 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `expense_line_types`
--

LOCK TABLES `expense_line_types` WRITE;
/*!40000 ALTER TABLE `expense_line_types` DISABLE KEYS */;
INSERT INTO `expense_line_types` VALUES (1,'Refuse','Municipal Refuse Expenses','No',0.00),(3,'Financials (Cyprus)','Annual Auditing Fees Cyprus - Alivente','Yes',2810.00),(4,'Prop Tax (Cyprus)','Immovable Property Tax (Cyprus)','No',0.00),(5,'Communal Fees 1','First Communal Fee Payment','No',0.00),(6,'Communal Fees 2','Second Communal Fee Payment','No',0.00),(7,'Insurance (Cyprus)','Annual Insurance','No',0.00),(8,'Company Tax','Company Tax (Cyprus)','Yes',7000.00),(9,'Property Manager','Property Manager - Stella','Yes',500.00),(16,'Agent Commission','Agent Commission (Spain)','No',NULL),(17,'Financials (Greece)','Annual Audit Fees Greece','Yes',2480.00),(18,'Financials (Spain)','Annual Audit Fees Spain','No',NULL),(20,'Company Fee','Annual Company Fee Cyprus','Yes',0.00),(21,'Electricity','Electricity','No',NULL),(22,'Water','Water','No',NULL),(23,'Cleaning Costs','Cleaning Costs','No',NULL),(24,'Garden Maint.','Garden Maintenance','No',0.00),(25,'Internet / TV','Internet / TV','No',NULL),(26,'Property Mgmt Fee','Property Management Fee','No',0.00),(27,'Depreciation','Depreciation','Yes',1000.00),(28,'Prop Tax (Greece)','Immovable Property Tax Greece','Yes',714.33),(29,'Insurance (Greece)','Insurance Greece','Yes',713.46),(30,'Insurance (Spain)','Insurance Spain','No',0.00);
/*!40000 ALTER TABLE `expense_line_types` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `expense_types`
--

DROP TABLE IF EXISTS `expense_types`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `expense_types` (
  `expense_types_id` int NOT NULL AUTO_INCREMENT,
  `expense_types_name` varchar(255) DEFAULT NULL,
  `expense_types_jan` varchar(3) DEFAULT NULL,
  `expense_types_feb` varchar(3) DEFAULT NULL,
  `expense_types_mar` varchar(3) DEFAULT NULL,
  `expense_types_apr` varchar(3) DEFAULT NULL,
  `expense_types_may` varchar(3) DEFAULT NULL,
  `expense_types_jun` varchar(3) DEFAULT NULL,
  `expense_types_jul` varchar(3) DEFAULT NULL,
  `expense_types_aug` varchar(3) DEFAULT NULL,
  `expense_types_sep` varchar(3) DEFAULT NULL,
  `expense_types_oct` varchar(3) DEFAULT NULL,
  `expense_types_nov` varchar(3) DEFAULT NULL,
  `expense_types_dec` varchar(3) DEFAULT NULL,
  PRIMARY KEY (`expense_types_id`)
) ENGINE=InnoDB AUTO_INCREMENT=21 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `expense_types`
--

LOCK TABLES `expense_types` WRITE;
/*!40000 ALTER TABLE `expense_types` DISABLE KEYS */;
INSERT INTO `expense_types` VALUES (1,'Monthly','Yes','Yes','Yes','Yes','Yes','Yes','Yes','Yes','Yes','Yes','Yes','Yes'),(2,'Quarterly','Yes','No','No','Yes','No','No','Yes','No','No','Yes','No','No'),(3,'Summer Monthly','No','No','No','No','Yes','Yes','Yes','Yes','Yes','Yes','No','No'),(4,'Summer Bi-Monthly','No','No','No','No','No','Yes','No','Yes','No','Yes','No','No'),(5,'Six Monthly','Yes','No','No','No','No','No','Yes','No','No','No','No','No'),(6,'January','Yes','No','No','No','No','No','No','No','No','No','No','No'),(7,'February','No','Yes','No','No','No','No','No','No','No','No','No','No'),(8,'March','No','No','Yes','No','No','No','No','No','No','No','No','No'),(9,'April','No','No','No','Yes','No','No','No','No','No','No','No','No'),(10,'May','No','No','No','No','Yes','No','No','No','No','No','No','No'),(11,'June','No','No','No','No','No','Yes','No','No','No','No','No','No'),(12,'July','No','No','No','No','No','No','Yes','No','No','No','No','No'),(13,'August','No','No','No','No','No','No','No','Yes','No','No','No','No'),(14,'September','No','No','No','No','No','No','No','No','Yes','No','No','No'),(15,'October','No','No','No','No','No','No','No','No','No','Yes','No','No'),(16,'November','No','No','No','No','No','No','No','No','No','No','Yes','No'),(17,'December','No','No','No','No','No','No','No','No','No','No','No','Yes');
/*!40000 ALTER TABLE `expense_types` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `invoice`
--

DROP TABLE IF EXISTS `invoice`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `invoice` (
  `invoice_id` int NOT NULL AUTO_INCREMENT,
  `invoice_date` date DEFAULT NULL,
  `invoice_paid` varchar(255) DEFAULT NULL,
  `tenant_id` int NOT NULL,
  PRIMARY KEY (`invoice_id`),
  KEY `invoice_tenant_id_71dc6f30_fk_tenant_tenant_id` (`tenant_id`),
  CONSTRAINT `invoice_tenant_id_71dc6f30_fk_tenant_tenant_id` FOREIGN KEY (`tenant_id`) REFERENCES `tenant` (`tenant_id`)
) ENGINE=InnoDB AUTO_INCREMENT=57 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `invoice`
--

LOCK TABLES `invoice` WRITE;
/*!40000 ALTER TABLE `invoice` DISABLE KEYS */;
INSERT INTO `invoice` VALUES (1,'2024-12-01','Yes',1),(2,'2024-12-01','Yes',2),(3,'2024-12-01','Yes',3),(4,'2024-11-01','No',3),(5,'2024-10-01','Yes',3),(6,'2024-09-01','Yes',3),(7,'2024-08-01','Yes',3),(8,'2024-12-01','Yes',4),(9,'2025-01-01','Yes',5),(10,'2024-11-01','No',9),(11,'2024-10-01','No',9),(12,'2024-08-01','No',10),(13,'2024-09-01','No',10),(14,'2025-05-01','No',1),(15,'2025-05-01','No',2),(16,'2025-05-01','No',3),(17,'2025-05-01','No',4),(18,'2025-05-01','Yes',5),(19,'2025-05-01','No',6),(20,'2025-05-01','No',7),(21,'2025-05-01','No',8),(49,'2025-06-01','No',1),(50,'2025-06-01','No',2),(51,'2025-06-01','No',3),(52,'2025-06-01','No',4),(53,'2025-06-01','Yes',5),(54,'2025-06-01','No',6),(55,'2025-06-01','No',7),(56,'2025-06-01','No',8);
/*!40000 ALTER TABLE `invoice` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `issues`
--

DROP TABLE IF EXISTS `issues`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `issues` (
  `issues_id` int NOT NULL AUTO_INCREMENT,
  `issues_heading` varchar(255) DEFAULT NULL,
  `issues_description` varchar(255) DEFAULT NULL,
  `issues_date_logged` date DEFAULT NULL,
  `issues_status` varchar(255) DEFAULT NULL,
  `issues_resolution_date` date DEFAULT NULL,
  `issues_resolving_user` varchar(255) DEFAULT NULL,
  `prop_id` int NOT NULL,
  PRIMARY KEY (`issues_id`),
  KEY `issues_prop_id_c0a64176_fk_prop_prop_id` (`prop_id`),
  CONSTRAINT `issues_prop_id_c0a64176_fk_prop_prop_id` FOREIGN KEY (`prop_id`) REFERENCES `prop` (`prop_id`)
) ENGINE=InnoDB AUTO_INCREMENT=51 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `issues`
--

LOCK TABLES `issues` WRITE;
/*!40000 ALTER TABLE `issues` DISABLE KEYS */;
INSERT INTO `issues` VALUES (1,'Painting of Reception','Have to repaint the reception due to water damage.','2024-11-24','Resolved','2025-07-15','',1),(2,'Tiling of Balcony','Have to retile balcony to stop water going through.','2024-12-09','Issue','1900-01-01','',4),(3,'Replace Airconditioner','Need to replace the airconditioner in the Boardroom','2024-10-15','Resolved','2025-07-15','DM',2),(4,'Clean Reception','Need to take Princess to clean the reception','2024-11-16','Resolved','2025-07-15','DM',2),(5,'Sealing of Door','Have to seal door so that water does not come through','2024-11-20','Unresolved','2025-05-14','',1),(6,'Mould on Ceiling','Humidity in Bedroom','2024-06-20','Resolved','2025-07-15','DM',5),(18,'Water Leak','Water leaking from the solar panels','2025-02-04','Issue','1900-01-01','',6),(26,'Passage Light not Working','Lights in passage don\'t automatically go on.','2025-02-04','Unresolved','1900-01-01',NULL,10),(34,'Kitchen Tap Leaking','The kitchen tap is leaking onto the floor','2025-02-11','Unresolved','1900-01-01',NULL,9),(35,'Pool needs Resurfacing urgently','The entire inside of the pool needs resurfacing...','2025-05-06','Resolved','2025-07-15',NULL,7),(36,'Testing Issue','Testing Issue','2025-05-06','Unresolved','1900-01-01',NULL,9),(48,'Problem with the Built in A/C','Have to replace the A/C','2025-06-05','Unresolved','2025-06-05',NULL,12),(49,'Test Issue','Test Issue','2025-06-05','Unresolved','1900-01-01',NULL,12),(50,'Aircon Malfunctioning, no cold air','The aircon has a big problem and not cooling well.','2025-06-26','Unresolved','1900-01-01',NULL,1);
/*!40000 ALTER TABLE `issues` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `issues_details`
--

DROP TABLE IF EXISTS `issues_details`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `issues_details` (
  `issues_details_id` int NOT NULL AUTO_INCREMENT,
  `issues_details_comment` varchar(255) DEFAULT NULL,
  `issues_details_user` varchar(255) DEFAULT NULL,
  `issues_details_date` date DEFAULT NULL,
  `issues_id` int NOT NULL,
  PRIMARY KEY (`issues_details_id`),
  KEY `issues_details_issues_id_f43987e8_fk_issues_issues_id` (`issues_id`),
  CONSTRAINT `issues_details_issues_id_f43987e8_fk_issues_issues_id` FOREIGN KEY (`issues_id`) REFERENCES `issues` (`issues_id`)
) ENGINE=InnoDB AUTO_INCREMENT=83 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `issues_details`
--

LOCK TABLES `issues_details` WRITE;
/*!40000 ALTER TABLE `issues_details` DISABLE KEYS */;
INSERT INTO `issues_details` VALUES (1,'OK.  Perfect.  Confirm a date for next month for him to come and complete.','DM','2024-12-04',1),(2,'Spoke to Marko, he will send someone to address this right away.','DM','2024-12-01',1),(3,'Marko confirmed that Vasilli would come today, but Vasilli did not come.  Will  call Marko again.','SS','2024-12-01',1),(4,'This is urgent, please ensure that we resolve this ASAP.','DM','2024-12-02',1),(5,'I spoke to Marko.  He went past.  He says that we need to wait for the slab to dry out first.','SS','2024-12-03',1),(6,'We need to replace the airconditioner with a 24,000 BTU Bosch unit.','SS','2024-11-18',3),(7,'Princess completed the cleaning','SS','2024-12-23',4),(8,'We will need to uplift all of the old tiles on the balcony','SS','2024-12-09',2),(9,'What is the toatl cost for this work?','DM','2024-12-10',2),(10,'I will speak to Mathew to get a quote','SS','2024-12-04',5),(11,'Running de-humidifiers','SS','2024-11-05',6),(12,'Test Comment','DM','2025-02-03',6),(13,'This is really working like a bomb.','DM','2025-02-03',2),(14,'Called Mr. Vangeli.  He will come through tomorrow.','DM','2025-02-04',18),(15,'Plumber came.  Resolved the issue.  Busy testing.','DM','2025-02-04',18),(17,'Issue still persists.','DM','2025-02-04',6),(18,'The automatic sensor that switches on the lights is not working.','DM','2025-02-04',26),(19,'Called the electrician.  He will replace the sensor.','DM','2025-02-04',26),(30,'Will send Vangeli to take a look.','DM','2025-02-11',34),(31,'Testing out the comment section','DM','2025-05-04',4),(32,'When will this be resolved','DM','2025-05-04',6),(33,'Testing new functionality','DM','2025-05-04',6),(34,'New comment added lately','DM','2025-05-04',3),(35,'Another comment','DM','2025-05-04',3),(36,'Vangeli will replace the tap','DM','2025-05-05',34),(37,'Quote for Euro 500','DM','2025-05-05',5),(38,'Approved quote','DM','2025-05-05',5),(39,'Tap replaced','DM','2025-05-05',34),(40,'Paid the supplier','DM','2025-05-05',3),(41,'Another test here','DM','2025-05-05',6),(42,'Payment was returned','DM','2025-05-05',3),(43,'Need to bring a technician to examine the inside of the pool so as to resurface the entire area.  This is urgent and must be addressed right away.','DM','2025-05-06',35),(44,'Not sure when the technician will come to examine.','DM','2025-05-06',35),(45,'New comment','DM','2025-05-06',35),(46,'New Comment','SS','2025-05-06',5),(75,'Will get Zach to give a quote','DM','2025-05-14',5),(76,'Too expensive','DM','2025-05-14',35),(77,'Speak to agent about changing the a/c','DM','2025-06-05',48),(78,'Speak to tenant','DM','2025-06-23',1),(79,'New Test Comment','DM','2025-06-24',5),(80,'New Test Comment','DM','2025-06-26',50),(81,'Going to try and fix the issue','DM','2025-07-15',36),(82,'New Test Issue.  Problem being worked on.','DM','2025-07-15',49);
/*!40000 ALTER TABLE `issues_details` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `petty_cash`
--

DROP TABLE IF EXISTS `petty_cash`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `petty_cash` (
  `petty_cash_id` int NOT NULL AUTO_INCREMENT,
  `petty_cash_date` date DEFAULT NULL,
  `petty_cash_description` varchar(55) DEFAULT NULL,
  `petty_cash_amount` decimal(6,2) DEFAULT NULL,
  `petty_cash_dr_cr` varchar(2) DEFAULT NULL,
  PRIMARY KEY (`petty_cash_id`)
) ENGINE=InnoDB AUTO_INCREMENT=50 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `petty_cash`
--

LOCK TABLES `petty_cash` WRITE;
/*!40000 ALTER TABLE `petty_cash` DISABLE KEYS */;
INSERT INTO `petty_cash` VALUES (1,'2024-07-01','Opening Balance',51.29,'DR'),(2,'2024-07-03','Apollonio: labour for carrying washing machine upstairs',30.00,'CR'),(3,'2024-07-10','Alivente: Top Up',100.00,'DR'),(4,'2024-08-16','Sklaveniti 2 x antimould sprays for Lykavitto storeroom',10.94,'CR'),(5,'2024-08-17','Princess Lykavitto cleaned storeroom',15.00,'CR'),(6,'2024-08-17','Bought rubbish bags for Lykavitto @ Green Tree',1.29,'CR'),(39,'2025-01-08','Foti Pitta: Balance of Levies and Ins. paid by Stella',5.00,'CR'),(40,'2025-01-21','Euro 200 Deposited for Sofa Cushions - Palikaridi',200.00,'DR'),(41,'2025-01-28','Palikaridi: Cushion payment. Euro 238, no change.',240.00,'CR'),(42,'2025-01-21','Apollonio - Demetri: Paid for delivery of ACs (Scandia)',28.00,'CR');
/*!40000 ALTER TABLE `petty_cash` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `prop`
--

DROP TABLE IF EXISTS `prop`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `prop` (
  `prop_id` int NOT NULL AUTO_INCREMENT,
  `prop_name` varchar(255) DEFAULT NULL,
  `prop_address1` varchar(255) DEFAULT NULL,
  `prop_address2` varchar(255) DEFAULT NULL,
  `prop_suburb` varchar(255) DEFAULT NULL,
  `prop_city` varchar(255) DEFAULT NULL,
  `prop_province` varchar(255) DEFAULT NULL,
  `prop_country` varchar(255) DEFAULT NULL,
  `prop_pcode` varchar(255) DEFAULT NULL,
  `prop_floor_area` int DEFAULT NULL,
  `prop_year_built` int DEFAULT NULL,
  `prop_status` varchar(255) DEFAULT NULL,
  `prop_available_for_rent` varchar(255) DEFAULT NULL,
  `prop_title_deed` varchar(100) DEFAULT NULL,
  `prop_title_deed_status` varchar(255) DEFAULT NULL,
  `prop_electricity` varchar(255) DEFAULT NULL,
  `prop_water` varchar(255) DEFAULT NULL,
  `prop_refuse` varchar(255) DEFAULT NULL,
  `prop_property_tax` varchar(255) DEFAULT NULL,
  `prop_sewerage` varchar(255) DEFAULT NULL,
  `prop_insurance` varchar(255) DEFAULT NULL,
  `prop_latitude` decimal(10,8) DEFAULT NULL,
  `prop_longitude` decimal(11,8) DEFAULT NULL,
  PRIMARY KEY (`prop_id`)
) ENGINE=InnoDB AUTO_INCREMENT=25 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `prop`
--

LOCK TABLES `prop` WRITE;
/*!40000 ALTER TABLE `prop` DISABLE KEYS */;
INSERT INTO `prop` VALUES (1,'Palikaridi','Apartment 201','Evagora Palikaridi 3','Agios Dometios','Nicosia','Nicosia','Cyprus','2369',88,2010,'Active','Yes','properties/title_deeds/prop_1_palikaridi_title_deed.pdf','Yes','Meter: 962943','090 741 321 158 970','05 000 723 5','282 833 73','Not Applicable','699455',35.16868826,33.33144077),(2,'Foti Pitta','Apartment 204','Foti Pitta 13','Engomi','Nicosia','Nicosia','Cyprus','2408',90,2000,'Active','Yes','properties/title_deeds/prop_2_foti-pitta_title_deed.pdf','Yes','Not Available','0905964 2221946 0','283373/3/21','283373/3/21','Not Applicable','699456',35.16685523,33.33394039),(3,'Pindarou','Apartment 701, Vamiko/Tymvio Tower','Pindarou 23',NULL,'Nicosia','Nicosia','Cyprus','1060',165,1982,'Active','Yes','properties/title_deeds/prop_3_pindarou_title_deed.pdf','Yes','Not Available','0205184 2310020 5','251827/3/21','251827/3/21','Not Applicable','699452',35.16695609,33.36754458),(4,'Eleftheroupoleos','Flat 16, Oriana Court','Elftheroupoleos 6','Strovolos','Nicosia','Nicosia','Cyprus','2001',140,1973,'Active','Yes','properties/title_deeds/prop_4_eleftheroupoleos_title_deed.pdf','Yes','Meter: 211976','0101770 1827552 7','266521','266521','Not Available','699453',35.15676404,33.36739410),(5,'Apolloneon - Demetri','Office 103','Agias Annas 4','Strovolos','Nicosia','Nicosia','Cyprus','2054',77,2010,'Active','Yes','properties/title_deeds/prop_5_apolloneon-demetri_title_deed.pdf','Yes','Not Available','Not Available','Not Available','Not Available','Not Available','Not Insured',35.14543901,33.32086772),(6,'Dikaiosynis','Dikaiosynis 13A','None','Engomi','Nicosia','Nicosia','Cyprus','2412',367,2007,'Inactive','No','properties/title_deeds/prop_6_dikaiosynis_title_deed.pdf','Yes','295 910 696 29','170 796 721 187 079','309760/2/9','309760/2/9','241 476 700 012 00','699460',35.15384590,33.31996930),(7,'Ionion - Villa 24','Ionion Seafront Villas, Villa 24','Aristoteli Valaoriti 7','Agia Thekla','Sotira','Famagusta','Cyprus','5390',127,2007,'Active','No','properties/title_deeds/prop_7_ionion-villa-24_title_deed.pdf','Yes','384 193 123 01','99-009-0007-24-0554 or 283373','02-011-007-00-024-01A','99-009-0007-24-0554 or 283373','Not Applicable','699458',34.97238998,33.90244104),(8,'Ionion - Villa H4','Ionion Seafront Villas, Villa H4','Aristoteli Valaoriti 7','Agia Thekla','Sotira','Famagusta','Cyprus','5390',186,2014,'Inactive','No','properties/title_deeds/prop_8_ionion-villa-h4_title_deed.pdf','Yes','689 707 644 91','99-009-0007-00-0H04 or 283373','02-011-007-00-0H4-01A','99-009-0007-00-0H04 or 283373','Not Applicable','699457',34.97278729,33.90407807),(9,'Athens - First Floor','First Floor Apartment','Afaias 15','Palaio Psychiko','Athens','Attiki','Greece','15452',121,1974,'Active','Yes','properties/title_deeds/prop_9_athens-first-floor_title_deed.pdf','Yes','Meter: 3138572','Meter: A97M44812','Not Available','Not Available','Not Available','361145',38.01645744,23.76472632),(10,'Athens - Second Floor','Second Floor Apartment','Afaias 15','Palaio Psychiko','Athens','Attiki','Greece','15452',121,1974,'Active','Yes','properties/title_deeds/prop_10_athens-second-floor_title_deed.pdf','Yes','Meter: 3138573','Meter: A96E64201','Not Available','Not Available','Not Available','361145',38.01645321,23.76455914),(11,'Athens - Third Floor','Third Floor Apartment','Afaias 15','Palaio Psychiko','Athens','Attiki','Greece','15452',121,1974,'Active','Yes','properties/title_deeds/prop_11_athens-third-floor_title_deed.pdf','Yes','Meter: 3138574','Meter: A97M44827','Not Available','Not Available','Not Available','361145',38.01645744,23.76441043),(12,'Spain - Eusebi Guell','Plaza Eusebi Guell 12','Bajos 1','Pedralbes','Barcelona','Barcelona','Spain','8034',81,1978,'Active','Yes','properties/title_deeds/prop_12_spain-eusebi-guell_title_deed.pdf','Yes','Not Available','Not Available','Not Available','Not Available','Not Available','660056223',41.39074437,2.11530973);
/*!40000 ALTER TABLE `prop` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `prop_values`
--

DROP TABLE IF EXISTS `prop_values`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `prop_values` (
  `prop_values_id` int NOT NULL AUTO_INCREMENT,
  `prop_values_purchase_price` int DEFAULT NULL,
  `prop_values_current_value` int DEFAULT NULL,
  `prop_id` int NOT NULL,
  PRIMARY KEY (`prop_values_id`),
  KEY `prop_values_prop_id_30ef5509_fk_prop_prop_id` (`prop_id`),
  CONSTRAINT `prop_values_prop_id_30ef5509_fk_prop_prop_id` FOREIGN KEY (`prop_id`) REFERENCES `prop` (`prop_id`)
) ENGINE=InnoDB AUTO_INCREMENT=18 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `prop_values`
--

LOCK TABLES `prop_values` WRITE;
/*!40000 ALTER TABLE `prop_values` DISABLE KEYS */;
INSERT INTO `prop_values` VALUES (3,500000,800000,6),(4,317500,450000,7),(5,275000,320000,4),(6,146500,200000,2),(7,162000,200000,5),(8,200000,250000,9),(9,250000,300000,10),(10,260000,300000,11),(11,380000,420000,12),(12,140000,200000,1),(13,375000,425000,3),(14,1035000,2200000,8);
/*!40000 ALTER TABLE `prop_values` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `revenue`
--

DROP TABLE IF EXISTS `revenue`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `revenue` (
  `revenue_id` int NOT NULL AUTO_INCREMENT,
  `revenue_amount` decimal(8,2) DEFAULT NULL,
  `revenue_jan` decimal(8,2) DEFAULT NULL,
  `revenue_feb` decimal(8,2) DEFAULT NULL,
  `revenue_mar` decimal(8,2) DEFAULT NULL,
  `revenue_apr` decimal(8,2) DEFAULT NULL,
  `revenue_may` decimal(8,2) DEFAULT NULL,
  `revenue_jun` decimal(8,2) DEFAULT NULL,
  `revenue_jul` decimal(8,2) DEFAULT NULL,
  `revenue_aug` decimal(8,2) DEFAULT NULL,
  `revenue_sep` decimal(8,2) DEFAULT NULL,
  `revenue_oct` decimal(8,2) DEFAULT NULL,
  `revenue_nov` decimal(8,2) DEFAULT NULL,
  `revenue_dec` decimal(8,2) DEFAULT NULL,
  `prop_id` int NOT NULL,
  `revenue_line_types_id` int NOT NULL,
  `revenue_types_id` int NOT NULL,
  PRIMARY KEY (`revenue_id`),
  KEY `revenue_prop_id_50e177ae_fk_prop_prop_id` (`prop_id`),
  KEY `revenue_revenue_line_types_i_030016a9_fk_revenue_l` (`revenue_line_types_id`),
  KEY `revenue_revenue_types_id_c2b6dd80_fk_revenue_t` (`revenue_types_id`),
  CONSTRAINT `revenue_prop_id_50e177ae_fk_prop_prop_id` FOREIGN KEY (`prop_id`) REFERENCES `prop` (`prop_id`),
  CONSTRAINT `revenue_revenue_line_types_i_030016a9_fk_revenue_l` FOREIGN KEY (`revenue_line_types_id`) REFERENCES `revenue_line_types` (`revenue_line_types_id`),
  CONSTRAINT `revenue_revenue_types_id_c2b6dd80_fk_revenue_t` FOREIGN KEY (`revenue_types_id`) REFERENCES `revenue_types` (`revenue_types_id`)
) ENGINE=InnoDB AUTO_INCREMENT=22 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `revenue`
--

LOCK TABLES `revenue` WRITE;
/*!40000 ALTER TABLE `revenue` DISABLE KEYS */;
INSERT INTO `revenue` VALUES (1,945.00,945.00,945.00,945.00,945.00,945.00,945.00,945.00,945.00,945.00,945.00,945.00,945.00,1,1,1),(2,850.00,850.00,850.00,850.00,850.00,850.00,850.00,850.00,850.00,850.00,850.00,850.00,850.00,2,1,1),(3,1250.00,1250.00,1250.00,1250.00,1250.00,1250.00,1250.00,1250.00,1250.00,1250.00,1250.00,1250.00,1250.00,3,1,1),(4,1064.00,1064.00,1064.00,1064.00,1064.00,1064.00,1064.00,1064.00,1064.00,1064.00,1064.00,1064.00,1064.00,4,1,1),(5,750.00,750.00,750.00,750.00,750.00,750.00,750.00,750.00,750.00,750.00,750.00,750.00,750.00,5,1,1),(6,3500.00,NULL,NULL,NULL,NULL,3500.00,3500.00,3500.00,3500.00,3500.00,3500.00,NULL,NULL,7,1,2),(7,925.00,925.00,925.00,925.00,925.00,925.00,925.00,925.00,925.00,925.00,925.00,925.00,925.00,9,1,1),(8,1180.00,1180.00,1180.00,1180.00,1180.00,1180.00,1180.00,1180.00,1180.00,1180.00,1180.00,1180.00,1180.00,10,1,1),(9,1030.00,1030.00,1030.00,1030.00,1030.00,1030.00,1030.00,1030.00,1030.00,1030.00,1030.00,1030.00,1030.00,11,1,1),(10,1300.00,1300.00,1300.00,1300.00,1300.00,1300.00,1300.00,1300.00,1300.00,1300.00,1300.00,1300.00,1300.00,12,1,1),(17,30.00,30.00,30.00,30.00,30.00,30.00,30.00,30.00,30.00,30.00,30.00,30.00,30.00,5,5,1),(18,35.00,35.00,35.00,35.00,35.00,35.00,35.00,35.00,35.00,35.00,35.00,35.00,35.00,4,5,1),(19,30.00,30.00,30.00,30.00,30.00,30.00,30.00,30.00,30.00,30.00,30.00,30.00,30.00,2,5,1),(20,30.00,30.00,30.00,30.00,30.00,30.00,30.00,30.00,30.00,30.00,30.00,30.00,30.00,1,5,1),(21,45.00,45.00,45.00,45.00,45.00,45.00,45.00,45.00,45.00,45.00,45.00,45.00,45.00,3,5,1);
/*!40000 ALTER TABLE `revenue` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `revenue_line_types`
--

DROP TABLE IF EXISTS `revenue_line_types`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `revenue_line_types` (
  `revenue_line_types_id` int NOT NULL AUTO_INCREMENT,
  `revenue_line_types_name` varchar(255) DEFAULT NULL,
  `revenue_line_types_description` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`revenue_line_types_id`)
) ENGINE=InnoDB AUTO_INCREMENT=7 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `revenue_line_types`
--

LOCK TABLES `revenue_line_types` WRITE;
/*!40000 ALTER TABLE `revenue_line_types` DISABLE KEYS */;
INSERT INTO `revenue_line_types` VALUES (1,'Rental','Rental Income'),(5,'Levies','Levies');
/*!40000 ALTER TABLE `revenue_line_types` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `revenue_types`
--

DROP TABLE IF EXISTS `revenue_types`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `revenue_types` (
  `revenue_types_id` int NOT NULL AUTO_INCREMENT,
  `revenue_types_name` varchar(255) DEFAULT NULL,
  `revenue_types_jan` varchar(3) DEFAULT NULL,
  `revenue_types_feb` varchar(3) DEFAULT NULL,
  `revenue_types_mar` varchar(3) DEFAULT NULL,
  `revenue_types_apr` varchar(3) DEFAULT NULL,
  `revenue_types_may` varchar(3) DEFAULT NULL,
  `revenue_types_jun` varchar(3) DEFAULT NULL,
  `revenue_types_jul` varchar(3) DEFAULT NULL,
  `revenue_types_aug` varchar(3) DEFAULT NULL,
  `revenue_types_sep` varchar(3) DEFAULT NULL,
  `revenue_types_oct` varchar(3) DEFAULT NULL,
  `revenue_types_nov` varchar(3) DEFAULT NULL,
  `revenue_types_dec` varchar(3) DEFAULT NULL,
  PRIMARY KEY (`revenue_types_id`)
) ENGINE=InnoDB AUTO_INCREMENT=9 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `revenue_types`
--

LOCK TABLES `revenue_types` WRITE;
/*!40000 ALTER TABLE `revenue_types` DISABLE KEYS */;
INSERT INTO `revenue_types` VALUES (1,'Monthly','Yes','Yes','Yes','Yes','Yes','Yes','Yes','Yes','Yes','Yes','Yes','Yes'),(2,'Summer','No','No','No','No','Yes','Yes','Yes','Yes','Yes','Yes','No','No');
/*!40000 ALTER TABLE `revenue_types` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `supplier`
--

DROP TABLE IF EXISTS `supplier`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `supplier` (
  `supplier_id` int NOT NULL AUTO_INCREMENT,
  `supplier_contact_person` varchar(255) DEFAULT NULL,
  `supplier_contact_number` varchar(255) DEFAULT NULL,
  `supplier_email` varchar(255) DEFAULT NULL,
  `supplier_company_name` varchar(255) DEFAULT NULL,
  `supplier_role` varchar(255) DEFAULT NULL,
  `supplier_country` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`supplier_id`)
) ENGINE=InnoDB AUTO_INCREMENT=17 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `supplier`
--

LOCK TABLES `supplier` WRITE;
/*!40000 ALTER TABLE `supplier` DISABLE KEYS */;
INSERT INTO `supplier` VALUES (1,'Rita Zacharia','+357 99 922268','rita@ezoria.com','Ezoria','Property Manager','Cyprus'),(3,'Tommy','+357 99 611708','None','None','Electrician','Cyprus'),(4,'Vasilis Aggelatos','+30 694 747 0917','info@jkconstruction.gr','JK Construction','Handyman / Builder','Greece'),(5,'Vasilis','+357 96 374203','None','Ezoria','Handyman','Cyprus'),(6,'Billy (Agia Thekla)','+357 99 104339','None','None','Plumber','Cyprus'),(7,'Vangeli','+357 99 851207','None','None','Plumber','Cyprus'),(8,'Mathew May','+357 97 795676','None','None','Handyman','Cyprus'),(9,'Alex','+357 96 975258','None','None','Airconditioning','Cyprus'),(10,'Niko (Agia Thekla)','+357 99 552315','None','None','Fumigator','Cyprus'),(11,'Panico (Agia Thekla)','+357 97 612130','None','None','Airconditioning','Cyprus'),(12,'Tareq','+357 99 822223','tareq@ezoria.com','Ezoria','Property Manager','Cyprus'),(13,'Costa (Agia Thekla)','+357 99 605309','None','None','Pool Maintenance','Cyprus'),(14,'Carles Berkinder','+34 93 209 81 09','carles@berkinder.com','Berkinder','Property Manager','Spain');
/*!40000 ALTER TABLE `supplier` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `tenant`
--

DROP TABLE IF EXISTS `tenant`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `tenant` (
  `tenant_id` int NOT NULL AUTO_INCREMENT,
  `tenant_type` varchar(255) DEFAULT NULL,
  `tenant_name` varchar(255) DEFAULT NULL,
  `tenant_contact_person` varchar(255) DEFAULT NULL,
  `tenant_contact_number` varchar(255) DEFAULT NULL,
  `tenant_email` varchar(255) DEFAULT NULL,
  `tenant_deposit` int DEFAULT NULL,
  `tenant_lease_start_date` date DEFAULT NULL,
  `tenant_lease_end_date` date DEFAULT NULL,
  `tenant_rental_type` varchar(255) DEFAULT NULL,
  `tenant_renewal` varchar(255) DEFAULT NULL,
  `tenant_renewal_period` int DEFAULT NULL,
  `tenant_rent` int DEFAULT NULL,
  `tenant_levies` int DEFAULT NULL,
  `tenant_payment_terms` int DEFAULT NULL,
  `tenant_current` varchar(255) DEFAULT NULL,
  `tenant_lease_agreement` varchar(100) DEFAULT NULL,
  `prop_id` int NOT NULL,
  `tenant_lease_agreement_status` varchar(255) DEFAULT NULL,
  `tenant_renewal_status` varchar(20) DEFAULT NULL,
  PRIMARY KEY (`tenant_id`),
  KEY `tenant_prop_id_e4de91fa_fk_prop_prop_id` (`prop_id`),
  CONSTRAINT `tenant_prop_id_e4de91fa_fk_prop_prop_id` FOREIGN KEY (`prop_id`) REFERENCES `prop` (`prop_id`)
) ENGINE=InnoDB AUTO_INCREMENT=25 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `tenant`
--

LOCK TABLES `tenant` WRITE;
/*!40000 ALTER TABLE `tenant` DISABLE KEYS */;
INSERT INTO `tenant` VALUES (1,'Individual','Sacha Mamou and James Luc-Sebaoun','Sacha Mamou and James Luc-Sebaoun','+33651200465 and +33769672329','sacha.mamou2@gmail.com and james.ls@icloud.com',930,'2024-09-01','2025-08-31','Monthly','Yes',60,945,30,0,'Yes','tenants/lease_agreements/tenant_1_sacha-mamou-and-james-luc-sebaoun_lease_agreement.pdf',1,'Lease Agreement Uploaded','declined'),(2,'Company','Capacitor Partners Limited','Michael Tyrimos','+35799660928','michael.tyrimos@capacitorpartners.com',1250,'2023-07-01','2026-06-30','Monthly','Yes',60,1250,45,0,'Yes','tenants/lease_agreements/tenant_2_capacitor-partners-limited_lease_agreement.pdf',3,'Lease Agreement Uploaded','pending'),(3,'Company','Assetworth Limited','Andreas Evangelou','+35799343298','andreas.evangelou@assetworth.com.cy',1064,'2024-09-01','2024-11-30','Monthly','Yes',60,1064,35,0,'Yes','tenants/lease_agreements/tenant_3_assetworth-limited_lease_agreement.pdf',4,'Lease Agreement Uploaded','pending'),(4,'Individual','Elisavet Solomonidou','Elisavet Solomonidou','+306948881091','solomonidou.elisabeth@yahoo.com',850,'2024-05-01','2026-06-30','Monthly','Yes',60,850,30,0,'Yes','tenants/lease_agreements/tenant_4_elisavet-solomonidou_lease_agreement.pdf',2,'Lease Agreement Uploaded','pending'),(5,'Individual','Chrystalla Katelari and Antigoni Andreou','Chrystalla Katelari and Antigoni Andreou','+35799266001 and +35796272030','katelari_chrystalla@hotmail.com and antigoni_andreou@outlook.com',750,'2024-10-01','2026-09-30','Monthly','Yes',60,750,30,0,'Yes','tenants/lease_agreements/tenant_5_chrystalla-katelari-and-antigoni-andreou_lease_agreement.pdf',5,'Lease Agreement Uploaded','pending'),(6,'Individual','Anastasia Spiropoulou and Constantinos Souvatzoglou','Anastasia Spiropoulou and Constantinos Souvatzoglou','+30 99 999999','nastaziaspy@googlemail.com and k.souvatzoglou@gmail.com',875,'2025-03-01','2027-02-28','Monthly','Yes',60,925,0,0,'Yes','tenants/lease_agreements/tenant_6_anastasia-spiropoulou-and-constantinos-souvatzoglo_lea_ClRk3Qo.pdf',9,'Lease Agreement Uploaded','pending'),(7,'Individual','Tenant - Athens 2','XXX','+30 99 999999','XXX@XXX.com',999,'2024-09-01','2025-03-31','Monthly','Yes',60,999,99,0,'Yes','tenants/lease_agreements/tenant_7_tenant-athens-2_lease_agreement.pdf',10,'Lease Agreement Uploaded','pending'),(8,'Individual','Tenant - Athens 3','XXX','+30 99 999999','XXX@XXX.com',999,'2024-09-01','2027-08-31','Monthly','Yes',60,999,99,0,'Yes','tenants/lease_agreements/tenant_8_tenant-athens-3_lease_agreement.pdf',11,'Lease Agreement Uploaded','pending'),(9,'Individual','Tenant - Spain - Test 1 (Non)','XXX','+34 99 999999','XXX@XXX.com',999,'2024-09-01','2025-08-31','Monthly','Yes',60,999,99,0,'No','tenants/lease_agreements/tenant_9_tenant-spain-test-1-non_lease_agreement.pdf',12,'Lease Agreement Uploaded','pending'),(10,'Individual','Tenant - Spain - Test 2 (Active)','XXX','+34 99 999999','XXX@XXX.com',999,'2024-09-01','2024-10-31','Monthly','Yes',60,999,99,0,'No','tenants/lease_agreements/tenant_10_tenant-spain-test-2-active_lease_agreement.pdf',12,'Lease Agreement Uploaded','pending');
/*!40000 ALTER TABLE `tenant` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2025-07-18  6:44:02
