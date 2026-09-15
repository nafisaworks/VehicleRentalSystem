-- MySQL dump 10.13  Distrib 8.4.11, for macos15 (arm64)
--
-- Host: localhost    Database: vehicle_rental_db
-- ------------------------------------------------------
-- Server version	8.4.11

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `BOOKING`
--

DROP TABLE IF EXISTS `BOOKING`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `BOOKING` (
  `booking_id` int NOT NULL AUTO_INCREMENT,
  `customer_id` int NOT NULL,
  `vehicle_id` int NOT NULL,
  `employee_id` int DEFAULT NULL,
  `start_date` date NOT NULL,
  `end_date` date NOT NULL,
  `total_amount` decimal(10,2) NOT NULL,
  `booking_status` varchar(20) DEFAULT 'Pending',
  PRIMARY KEY (`booking_id`),
  KEY `customer_id` (`customer_id`),
  KEY `vehicle_id` (`vehicle_id`),
  KEY `employee_id` (`employee_id`),
  CONSTRAINT `booking_ibfk_1` FOREIGN KEY (`customer_id`) REFERENCES `CUSTOMER` (`customer_id`),
  CONSTRAINT `booking_ibfk_2` FOREIGN KEY (`vehicle_id`) REFERENCES `VEHICLE` (`vehicle_id`),
  CONSTRAINT `booking_ibfk_3` FOREIGN KEY (`employee_id`) REFERENCES `EMPLOYEE` (`employee_id`)
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `BOOKING`
--

LOCK TABLES `BOOKING` WRITE;
/*!40000 ALTER TABLE `BOOKING` DISABLE KEYS */;
INSERT INTO `BOOKING` VALUES (1,1,1,1,'2026-09-20','2026-09-22',5400.00,'Confirmed'),(2,2,2,2,'2026-09-21','2026-09-24',7500.00,'Confirmed'),(3,3,3,1,'2026-09-25','2026-09-27',4500.00,'Pending');
/*!40000 ALTER TABLE `BOOKING` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `CUSTOMER`
--

DROP TABLE IF EXISTS `CUSTOMER`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `CUSTOMER` (
  `customer_id` int NOT NULL AUTO_INCREMENT,
  `customer_name` varchar(100) NOT NULL,
  `email` varchar(100) NOT NULL,
  `phone` varchar(15) NOT NULL,
  `address` varchar(255) DEFAULT NULL,
  `password` varchar(100) NOT NULL,
  PRIMARY KEY (`customer_id`),
  UNIQUE KEY `email` (`email`)
) ENGINE=InnoDB AUTO_INCREMENT=11 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `CUSTOMER`
--

LOCK TABLES `CUSTOMER` WRITE;
/*!40000 ALTER TABLE `CUSTOMER` DISABLE KEYS */;
INSERT INTO `CUSTOMER` VALUES (1,'Rahul Kumar','rahul@gmail.com','9876543210','Chennai','rahul123'),(2,'Priya Sharma','priya@gmail.com','9876543211','Vellore','priya123'),(3,'Arjun Patel','arjun@gmail.com','9876543212','Bangalore','arjun123'),(4,'Sneha Reddy','sneha@gmail.com','9876543213','Hyderabad','sneha123'),(5,'Karan Singh','karan@gmail.com','9876543214','Mumbai','karan123');
/*!40000 ALTER TABLE `CUSTOMER` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `EMPLOYEE`
--

DROP TABLE IF EXISTS `EMPLOYEE`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `EMPLOYEE` (
  `employee_id` int NOT NULL AUTO_INCREMENT,
  `employee_name` varchar(100) NOT NULL,
  `email` varchar(100) NOT NULL,
  `phone` varchar(15) DEFAULT NULL,
  `role` varchar(50) NOT NULL,
  PRIMARY KEY (`employee_id`),
  UNIQUE KEY `email` (`email`)
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `EMPLOYEE`
--

LOCK TABLES `EMPLOYEE` WRITE;
/*!40000 ALTER TABLE `EMPLOYEE` DISABLE KEYS */;
INSERT INTO `EMPLOYEE` VALUES (1,'Admin One','admin1@rental.com','9000000001','Manager'),(2,'Admin Two','admin2@rental.com','9000000002','Booking Manager'),(3,'Staff One','staff1@rental.com','9000000003','Maintenance Staff');
/*!40000 ALTER TABLE `EMPLOYEE` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `MAINTENANCE`
--

DROP TABLE IF EXISTS `MAINTENANCE`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `MAINTENANCE` (
  `maintenance_id` int NOT NULL AUTO_INCREMENT,
  `vehicle_id` int NOT NULL,
  `employee_id` int DEFAULT NULL,
  `maintenance_date` date NOT NULL,
  `description` varchar(255) DEFAULT NULL,
  `cost` decimal(10,2) DEFAULT NULL,
  `maintenance_status` varchar(30) DEFAULT 'Completed',
  PRIMARY KEY (`maintenance_id`),
  KEY `vehicle_id` (`vehicle_id`),
  KEY `employee_id` (`employee_id`),
  CONSTRAINT `maintenance_ibfk_1` FOREIGN KEY (`vehicle_id`) REFERENCES `VEHICLE` (`vehicle_id`),
  CONSTRAINT `maintenance_ibfk_2` FOREIGN KEY (`employee_id`) REFERENCES `EMPLOYEE` (`employee_id`)
) ENGINE=InnoDB AUTO_INCREMENT=7 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `MAINTENANCE`
--

LOCK TABLES `MAINTENANCE` WRITE;
/*!40000 ALTER TABLE `MAINTENANCE` DISABLE KEYS */;
INSERT INTO `MAINTENANCE` VALUES (1,1,3,'2026-08-10','Oil change and general service',2500.00,'Completed'),(2,4,3,'2026-08-15','Brake inspection and replacement',4500.00,'Completed'),(3,7,3,'2026-09-01','Engine inspection',3000.00,'Completed');
/*!40000 ALTER TABLE `MAINTENANCE` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `PAYMENT`
--

DROP TABLE IF EXISTS `PAYMENT`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `PAYMENT` (
  `payment_id` int NOT NULL AUTO_INCREMENT,
  `booking_id` int NOT NULL,
  `payment_date` date NOT NULL,
  `amount` decimal(10,2) NOT NULL,
  `payment_method` varchar(30) NOT NULL,
  `payment_status` varchar(20) DEFAULT 'Pending',
  PRIMARY KEY (`payment_id`),
  KEY `booking_id` (`booking_id`),
  CONSTRAINT `payment_ibfk_1` FOREIGN KEY (`booking_id`) REFERENCES `BOOKING` (`booking_id`)
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `PAYMENT`
--

LOCK TABLES `PAYMENT` WRITE;
/*!40000 ALTER TABLE `PAYMENT` DISABLE KEYS */;
INSERT INTO `PAYMENT` VALUES (1,1,'2026-09-15',5400.00,'UPI','Paid'),(2,2,'2026-09-15',7500.00,'Credit Card','Paid'),(3,3,'2026-09-15',4500.00,'Cash','Pending');
/*!40000 ALTER TABLE `PAYMENT` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `VEHICLE`
--

DROP TABLE IF EXISTS `VEHICLE`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `VEHICLE` (
  `vehicle_id` int NOT NULL AUTO_INCREMENT,
  `vehicle_name` varchar(100) NOT NULL,
  `registration_no` varchar(20) NOT NULL,
  `type_id` int NOT NULL,
  `model_year` int DEFAULT NULL,
  `price_per_day` decimal(10,2) NOT NULL,
  `availability_status` varchar(20) DEFAULT 'Available',
  PRIMARY KEY (`vehicle_id`),
  UNIQUE KEY `registration_no` (`registration_no`),
  KEY `type_id` (`type_id`),
  CONSTRAINT `vehicle_ibfk_1` FOREIGN KEY (`type_id`) REFERENCES `VEHICLE_TYPE` (`type_id`)
) ENGINE=InnoDB AUTO_INCREMENT=9 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `VEHICLE`
--

LOCK TABLES `VEHICLE` WRITE;
/*!40000 ALTER TABLE `VEHICLE` DISABLE KEYS */;
INSERT INTO `VEHICLE` VALUES (1,'Honda City','TN01AB1234',1,2023,1800.00,'Available'),(2,'Hyundai Creta','TN02CD5678',2,2024,2500.00,'Available'),(3,'Maruti Swift','TN03EF9012',3,2023,1500.00,'Available'),(4,'Toyota Innova','TN04GH3456',2,2022,2800.00,'Available'),(5,'BMW 3 Series','TN05IJ7890',4,2024,5000.00,'Available'),(6,'Hyundai i20','TN06KL1234',3,2022,1600.00,'Available'),(7,'Mercedes C-Class','TN07MN5678',4,2023,6000.00,'Available'),(8,'Honda Amaze','TN08OP9012',1,2022,1700.00,'Available');
/*!40000 ALTER TABLE `VEHICLE` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `VEHICLE_TYPE`
--

DROP TABLE IF EXISTS `VEHICLE_TYPE`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `VEHICLE_TYPE` (
  `type_id` int NOT NULL AUTO_INCREMENT,
  `type_name` varchar(50) NOT NULL,
  `description` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`type_id`)
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `VEHICLE_TYPE`
--

LOCK TABLES `VEHICLE_TYPE` WRITE;
/*!40000 ALTER TABLE `VEHICLE_TYPE` DISABLE KEYS */;
INSERT INTO `VEHICLE_TYPE` VALUES (1,'Sedan','Comfortable four-door car'),(2,'SUV','Sport utility vehicle'),(3,'Hatchback','Compact city car'),(4,'Luxury','Premium luxury vehicle');
/*!40000 ALTER TABLE `VEHICLE_TYPE` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2026-09-12 12:40:37
