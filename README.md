# KohviLora
Solution to send small payloads from one machine (transmitter) to another (receiver). Uses LoRa technology with the help of mayeranalytics/pySX127x python library.

## CONFIGURATION
Use the config.ini file to set necessary properties for LoRa connection.


## USE
Start the program runner.py either with argument t/T (for transmitter functionality) or r/R (for receiver functionality). Use the optional argument -d/--debug to set the verbose logging as enabled.

When transmitting, the program searches the motor_log table for new records (records where the transmit is null), encodes them to ASCII code and sends them out using LoRa link. Transmitter is then waiting for ACK message. When received, the records are marked as sent and the program is ended. If ACK is not received, the records are left as they were and are sent next time when the transmitting session is started.

When receiving, the program continuously listens to the channel and when the payload is received, the CRC code is checked to see if the payload received is invalid or not. If not, the message is parsed to a readable form and saved to database. ACK is sent out. If not, nothing is done and module is switched back to continuous receive mode. 

## work in progress...