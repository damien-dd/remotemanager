# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'RemoteDevice'
        db.create_table(u'main_app_remotedevice', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('remotedevice_name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=30)),
            ('remotedevice_dev', self.gf('django.db.models.fields.CharField')(unique=True, max_length=20)),
        ))
        db.send_create_signal(u'main_app', ['RemoteDevice'])

        # Adding model 'USBRemoteDevice'
        db.create_table(u'main_app_usbremotedevice', (
            (u'remotedevice_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['main_app.RemoteDevice'], unique=True, primary_key=True)),
        ))
        db.send_create_signal(u'main_app', ['USBRemoteDevice'])

        # Adding model 'BluetoothRemoteDevice'
        db.create_table(u'main_app_bluetoothremotedevice', (
            (u'remotedevice_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['main_app.RemoteDevice'], unique=True, primary_key=True)),
            ('bluetoothremotedevice_mac', self.gf('django.db.models.fields.CharField')(unique=True, max_length=17)),
            ('bluetoothremotedevice_channel', self.gf('django.db.models.fields.IntegerField')(default=1)),
        ))
        db.send_create_signal(u'main_app', ['BluetoothRemoteDevice'])

        # Adding model 'Serie'
        db.create_table(u'main_app_serie', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('serie_name', self.gf('django.db.models.fields.CharField')(max_length=30)),
            ('serie_remotedevice', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['main_app.RemoteDevice'])),
            ('serie_tag', self.gf('django.db.models.fields.CharField')(max_length=2)),
            ('serie_type', self.gf('django.db.models.fields.CharField')(max_length=3)),
            ('serie_unit', self.gf('django.db.models.fields.CharField')(max_length=10)),
            ('serie_last_timestamp', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
        ))
        db.send_create_signal(u'main_app', ['Serie'])

        # Adding unique constraint on 'Serie', fields ['serie_remotedevice', 'serie_tag']
        db.create_unique(u'main_app_serie', ['serie_remotedevice_id', 'serie_tag'])

        # Adding model 'DataField'
        db.create_table(u'main_app_datafield', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('datafield_serie', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['main_app.Serie'])),
            ('datafield_nb_points', self.gf('django.db.models.fields.IntegerField')()),
            ('datafield_timestamp', self.gf('django.db.models.fields.DateTimeField')()),
            ('datafield_value', self.gf('django.db.models.fields.IntegerField')()),
        ))
        db.send_create_signal(u'main_app', ['DataField'])

        # Adding unique constraint on 'DataField', fields ['datafield_serie', 'datafield_timestamp']
        db.create_unique(u'main_app_datafield', ['datafield_serie_id', 'datafield_timestamp'])


    def backwards(self, orm):
        # Removing unique constraint on 'DataField', fields ['datafield_serie', 'datafield_timestamp']
        db.delete_unique(u'main_app_datafield', ['datafield_serie_id', 'datafield_timestamp'])

        # Removing unique constraint on 'Serie', fields ['serie_remotedevice', 'serie_tag']
        db.delete_unique(u'main_app_serie', ['serie_remotedevice_id', 'serie_tag'])

        # Deleting model 'RemoteDevice'
        db.delete_table(u'main_app_remotedevice')

        # Deleting model 'USBRemoteDevice'
        db.delete_table(u'main_app_usbremotedevice')

        # Deleting model 'BluetoothRemoteDevice'
        db.delete_table(u'main_app_bluetoothremotedevice')

        # Deleting model 'Serie'
        db.delete_table(u'main_app_serie')

        # Deleting model 'DataField'
        db.delete_table(u'main_app_datafield')


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