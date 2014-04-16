#include <stdlib.h>
#include <stdio.h>
#include <unistd.h>
#include <string.h>
#include <tempered.h>

/**
   This example shows how to enumerate the attached devices, print some
   information about them, and read their sensors once.
*/

/** Get and print the sensor values for a given device and sensor. */
int get_temperature(tempered_device *device, int sensor, float * tempC)
{
  int type = tempered_get_sensor_type( device, sensor );
  if ( type == TEMPERED_SENSOR_TYPE_NONE )
    {
      return 1;
    }
  if ( type & TEMPERED_SENSOR_TYPE_TEMPERATURE )
    {
      if ( tempered_get_temperature( device, sensor, tempC ) )
	{
	  return 0;
	}
      else
	{
	  printf("ERROR: Failed to get the temperature: %s\n",
		 tempered_error( device )
		 );
	  return -1;
	}
    }
  return 2;
}

/** Get and print information and sensor values for a given device. */
void read_device( struct tempered_device_list *dev )
{
  char *error = NULL;
  //TODO: only open devices once...
  tempered_device *device = tempered_open( dev, &error );
  if ( device == NULL )
    {
      printf( "Open failed, error: %s\n", error );
      free( error );
      return;
    }
  if ( !tempered_read_sensors( device ) )
    {
      printf(
	     "ERROR: Failed to read the sensors: %s\n",
	     tempered_error( device )
	     );
    }
  else
    {
      int sensor, sensors = tempered_get_sensor_count( device );
      float tempC;
      int err;
      for ( sensor = 0; sensor < sensors; sensor++ )
	{
	  err = get_temperature(device, sensor, &tempC);
	  if (err)
	    {
	      printf("ERROR: code %d\n", err);
	      continue;
	      //TODO: exit? cleanup?
	    }
	  printf("Device %s: Sensor %i: Temperature: %.2f°C\n",
		 dev->path, sensor, tempC);
	}
    }
  tempered_close( device );
}

int main( void )
{
  char *error = NULL;
  if ( !tempered_init( &error ) )
    {
      fprintf( stderr, "Failed to initialize libtempered: %s\n", error );
      free( error );
      return 1;
    }
	
  struct tempered_device_list *list = tempered_enumerate( &error );
  if ( list == NULL )
    {
      if ( error == NULL )
	{
	  printf( "No devices were found.\n" );
	}
      else
	{
	  fprintf( stderr, "Failed to enumerate devices: %s\n", error );
	  free( error );
	}
    }
  else
    {
      // Continually read each devices' sensors, sleeping in between
      struct tempered_device_list *dev;
      while (true)
	{
	  for ( dev = list ; dev != NULL ; dev = dev->next )
	    {
	      read_device( dev );
	    }
	  sleep(1);
	}
      tempered_free_device_list( list );
    }
	
  if ( !tempered_exit( &error ) )
    {
      fprintf( stderr, "Failed to shut down libtempered: %s\n", error );
      free( error );
      return 1;
    }
  return 0;
}
