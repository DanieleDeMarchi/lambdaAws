const {InfluxDB, Point, HttpError} = require('@influxdata/influxdb-client')


/*****
 * Lambda function che salva i dati inviati dai distpositivi in influxDb
 * 
 * Estrae misurazioni e crea i punti da inserire
 * 
 */

const token = ''
const org = ''
const bucket = ''
const url = 'https://eu-central-1-1.aws.cloud2.influxdata.com'

function estraiMisurazioni(tipi_misurazioni, mesurementObj){
  let points = []
  
  if (tipi_misurazioni.includes('net_io')) {
    let net_interfaces = mesurementObj.net_io
    
    net_interfaces.forEach(element => {
      
      let net_point = new Point('net_io').tag('net_interface', element.interface_name)
          .intField('sent_kbps', element.kbps_sent)
          .intField('recv_kbps', element.kbps_recv)
        
      points.push(net_point)
        
    });
	}
		
	if (tipi_misurazioni.includes('cpu_load')) {
      let cpu_point = new Point('cpu_load').floatField('cpu_load', mesurementObj.cpu_load.CpuLoad)
			points.push(cpu_point)
		}

	if (tipi_misurazioni.includes('memory_load')) {
    const pointRam = new Point('memory_load').tag('tipo_memoria', 'virtual_memory')
          .intField('total', mesurementObj.memory_load.total)
          .intField('used', mesurementObj.memory_load.total-mesurementObj.memory_load.available)

    const pointSwap = new Point('memory_load').tag('tipo_memoria', 'swap_memory')
          .intField('swap_total', mesurementObj.memory_load.swap_total)
          .intField('swap_used', mesurementObj.memory_load.swap_used)
          
    points.push(pointRam)
    points.push(pointSwap)
		}
		
		return points;
}


exports.handler = async (event) => {
    const writeApi = new InfluxDB({url, token}).getWriteApi(org, bucket, 's')
    
    console.log(event)
    
    let device_id = event.device_id
    let timestamp = event.unix_timestamp
    
    let points = estraiMisurazioni(event.measurement_type, event.measurement)
    
    console.log("Ok")
    
    points.forEach(punto =>{
      punto.tag("device_id", device_id).timestamp(timestamp)
      writeApi.writePoint(punto)
    });
    
    

    await writeApi
    .close()
    .then(() => {
        console.log('FINISHED')
    })
    .catch(e => {
        console.error(e)
        console.log('\\nFinished ERROR')
    })
  
  
    return;
};

