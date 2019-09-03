import time
import spidev

#SPI init

# We only have SPI bus 0
bus = 0
#Chip Select pin
CS = 0

# Enable SPI
spi = spidev.SpiDev()

# Open a connection to a specific bus and chip select pin
spi.open(bus, CS)

# Set SPI speed (100kHz) and mode
spi.max_speed_hz = 100000
spi.mode = 0

#Lora Commands
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
def LoraInit():
    #config LoRa
    #print("writing 0x80 (sleep, highFrq,LoRa) to reg config (0x01)")
    msg = [0x80 | 0x01, 0x80]
    result = spi.xfer2(msg)

    #high power tx mode
    #print("writing 0xFF to reg high power TX (0x09)")
    msg = [0x80 | 0x09,0xFF]
    result = spi.xfer2(msg)

    #verify Output Pin configuration
    #print("writing 0x00 to output PIN connection (0x40)")
    msg = [0x80 | 0x40, 0x00]
    result = spi.xfer2(msg)
    #print("Output Pin Config -> msg[0]: ",hex(msg[0]),"msg[1]: ",hex(msg[1]))
    print("Lora Initilized Succesfully")
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
def CheckMessage():
    msg = [0x00 | 0x12, 0x00]
    result = spi.xfer2(msg)
    if(result[1] & 0x40 == 0x40): #0x40 = Rx recived!
        #verify legitness
        msg = [0x00 | 0x13, 0x00]
        result = spi.xfer2(msg)
        numBytesReceived = result[1]
        if numBytesReceived > 10:
            #clear flag
            msg = [0x80 | 0x12, 0xFF]
            result = spi.xfer2(msg)
            return False
        return True
    elif(result[1] & 0x80 == 0x80 or result[1] & 0x20 == 0x20):
        #0x80 = RX timeout
        #0x50 = CRC error
        
        #clear flag
        msg = [0x80 | 0x12, 0xFF]
        result = spi.xfer2(msg)
        return False
    else:
        return False
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
def readMessage():
    #assume 'CheckMessage()' returned true
    
    #clear flag
    msg = [0x80 | 0x12, 0xFF]
    result = spi.xfer2(msg)

    #extract data - - - 
    msg = [0x00 | 0x13, 0x00]
    result = spi.xfer2(msg)
    numBytesReceived = result[1]
    msg = [0x00 | 0x10, 0x00]
    result = spi.xfer2(msg)
    storageLocation = result[1]

    #set fifo to storage location
    msg = [0x80 | 0x0D, storageLocation]
    result = spi.xfer2(msg)

    storageArray = []
    #extract data
    for x in range(numBytesReceived):
        msg = [0x00 | 0x00, 0x00]
        result = spi.xfer2(msg)
        storageArray.append(result[1])

    #reset FIFO ptr
    msg = [0x80 | 0x0D, 0x00]
    result = spi.xfer2(msg)

    return storageArray
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
def setRxMode():
    #print("writing SLEEP mode (0x81) to config register (0x01)")
    msg = [0x80 | 0x01,0x80]
    result = spi.xfer2(msg)

    #setup Rx fifo
    msg = [0x80 | 0x0D,0x00]
    result = spi.xfer2(msg)

    #set into Rx Continous Mode
    msg = [0x80 | 0x01,0x85]
    result = spi.xfer2(msg)
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
def LoraSendMessage( messageList, messageSize):
    #print("writing STBY mode (0x81) to config register (0x01)")
    msg = [0x80 | 0x01, 0x81]
    result = spi.xfer2(msg)

    #print("writing Tx_fifoPtr (0x80) to FifoPtr_address (0x0D)")
    msg = [0x80 | 0x0D,0x80]
    result = spi.xfer2(msg)

    #fillFifo
    for x in messageList:
        msg = [0x80 | 0x00,x]
        result = spi.xfer2(msg)
    #print("set payload length (in our case 0x03) to register (0x22)")
    msg = [0x80 | 0x22,messageSize]
    result = spi.xfer2(msg)

    #print("Put tranciver into TX mode")
    msg = [0x80 | 0x01, 0x83]
    result = spi.xfer2(msg)

    #wait until Tx is done
    msg = [0x00 | 0x12, 0x00]
    result = spi.xfer2(msg) 
    while(result[1] & 0x08 != 0x08):
        msg = [0x00 | 0x12, 0x00]
        result = spi.xfer2(msg)

    #clear Tx flag
    msg = [0x80 | 0x12, 0x08]
    result = spi.xfer2(msg) 

    #print
    print("LoRa       | Sent Message: {",end =" ")
    for x in messageList:
        print(hex(x),end =" ")
    print("}")
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
#init the tranciver
LoraInit()

#put into Rx-continous mode
setRxMode()

# if we receive a message, print & reply
while True:

    #check if we have received any message
    if CheckMessage() == True:
    
        #load list with received info 
        readMessageList = readMessage()
        
        #print data
        print("RX message: {",end =" ")
        for x in readMessageList:
            print(hex(x),end = " ")
        print("}")
        
        #message to reply
        SendMessage = [ 0x00, 0x01, 0x02, 0x03 ]
        
        LoraSendMessage(SendMessage, 4)
        
        #put back into Rx continous mode
        setRxMode()
      
