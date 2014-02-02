# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding field 'Serie.serie_last_update'
        db.add_column(u'main_app_serie', 'serie_last_update',
                      self.gf('django.db.models.fields.CharField')(default='', max_length=12),
                      keep_default=False)


    def backwards(self, orm):
        # Deleting field 'Serie.serie_last_update'
        db.delete_column(u'main_app_serie', 'serie_last_update')


    models = {
        u'main_app.bluetoothremotedevice': {
            'Meta': {'object_name': 'BluetoothRemoteDevice', '_ormbases': [u'main_app.RemoteDevice']},
            'bluetoothremotedevice_channel': ('django.db.models.fields.IntegerField', [], {'default': '1'}),
            'bluetoothremotedevice_mac': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '17'}),
            u'remotedevice_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['main_app.RemoteDevice']", 'unique': 'True', 'primary_key': 'True'})
        },
        u'main_app.datafield': {
            'Meta': {'unique_together': "(('datafield_serie', 'datafield_timestamp'),)", 'object_name': 'DataField'},
            'datafield_nb_points': ('django.db.models.fields.IntegerField', [], {}),
            'datafield_serie': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['main_app.Serie']"}),
            'datafield_timestamp': ('django.db.models.fields.DateTimeField', [], {}),
            'datafield_value': ('django.db.models.fields.IntegerField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        u'main_app.remotedevice': {
            'Meta': {'object_name': 'RemoteDevice'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'remotedevice_dev': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '20'}),
            'remotedevice_name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        u'main_app.serie': {
            'Meta': {'unique_together': "(('serie_remotedevice', 'serie_tag'),)", 'object_name': 'Serie'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'serie_last_timestamp': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'serie_last_update': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '12'}),
            'serie_name': ('django.db.models.fields.CharField', [], {'max_length': '30'}),
            'serie_remotedevice': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['main_app.RemoteDevice']"}),
            'serie_tag': ('django.db.models.fields.CharField', [], {'max_length': '2'}),
            'serie_type': ('django.db.models.fields.CharField', [], {'max_length': '3'}),
            'serie_unit': ('django.db.models.fields.CharField', [], {'max_length': '10'})
        },
        u'main_app.usbremotedevice': {
            'Meta': {'object_name': 'USBRemoteDevice', '_ormbases': [u'main_app.RemoteDevice']},
            u'remotedevice_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['main_app.RemoteDevice']", 'unique': 'True', 'primary_key': 'True'})
        }
    }

    complete_apps = ['main_app']