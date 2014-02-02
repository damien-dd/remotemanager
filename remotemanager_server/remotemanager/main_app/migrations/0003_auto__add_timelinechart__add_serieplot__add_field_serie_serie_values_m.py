# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'TimelineChart'
        db.create_table(u'main_app_timelinechart', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('timelinechart_title', self.gf('django.db.models.fields.CharField')(max_length=30)),
            ('timelinechart_yaxis_text', self.gf('django.db.models.fields.CharField')(max_length=30)),
        ))
        db.send_create_signal(u'main_app', ['TimelineChart'])

        # Adding model 'SeriePlot'
        db.create_table(u'main_app_serieplot', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('serieplot_serie', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['main_app.Serie'])),
            ('serieplot_timelinechart', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['main_app.TimelineChart'])),
            ('serieplot_color', self.gf('django.db.models.fields.CharField')(max_length=6)),
            ('serieplot_rank', self.gf('django.db.models.fields.IntegerField')(default=1)),
        ))
        db.send_create_signal(u'main_app', ['SeriePlot'])

        # Adding field 'Serie.serie_values_multiplier'
        db.add_column(u'main_app_serie', 'serie_values_multiplier',
                      self.gf('django.db.models.fields.FloatField')(default=1),
                      keep_default=False)

        # Adding field 'Serie.serie_values_offset'
        db.add_column(u'main_app_serie', 'serie_values_offset',
                      self.gf('django.db.models.fields.FloatField')(default=0),
                      keep_default=False)

        # Adding field 'Serie.serie_values_decimals'
        db.add_column(u'main_app_serie', 'serie_values_decimals',
                      self.gf('django.db.models.fields.IntegerField')(default=0),
                      keep_default=False)


    def backwards(self, orm):
        # Deleting model 'TimelineChart'
        db.delete_table(u'main_app_timelinechart')

        # Deleting model 'SeriePlot'
        db.delete_table(u'main_app_serieplot')

        # Deleting field 'Serie.serie_values_multiplier'
        db.delete_column(u'main_app_serie', 'serie_values_multiplier')

        # Deleting field 'Serie.serie_values_offset'
        db.delete_column(u'main_app_serie', 'serie_values_offset')

        # Deleting field 'Serie.serie_values_decimals'
        db.delete_column(u'main_app_serie', 'serie_values_decimals')


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
            'serie_last_update': ('django.db.models.fields.CharField', [], {'default': "'000000,000'", 'max_length': '12'}),
            'serie_name': ('django.db.models.fields.CharField', [], {'max_length': '30'}),
            'serie_remotedevice': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['main_app.RemoteDevice']"}),
            'serie_tag': ('django.db.models.fields.CharField', [], {'max_length': '2'}),
            'serie_type': ('django.db.models.fields.CharField', [], {'max_length': '3'}),
            'serie_unit': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
            'serie_values_decimals': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'serie_values_multiplier': ('django.db.models.fields.FloatField', [], {'default': '1'}),
            'serie_values_offset': ('django.db.models.fields.FloatField', [], {'default': '0'})
        },
        u'main_app.serieplot': {
            'Meta': {'object_name': 'SeriePlot'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'serieplot_color': ('django.db.models.fields.CharField', [], {'max_length': '6'}),
            'serieplot_rank': ('django.db.models.fields.IntegerField', [], {'default': '1'}),
            'serieplot_serie': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['main_app.Serie']"}),
            'serieplot_timelinechart': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['main_app.TimelineChart']"})
        },
        u'main_app.timelinechart': {
            'Meta': {'object_name': 'TimelineChart'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'timelinechart_series': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['main_app.Serie']", 'through': u"orm['main_app.SeriePlot']", 'symmetrical': 'False'}),
            'timelinechart_title': ('django.db.models.fields.CharField', [], {'max_length': '30'}),
            'timelinechart_yaxis_text': ('django.db.models.fields.CharField', [], {'max_length': '30'})
        },
        u'main_app.usbremotedevice': {
            'Meta': {'object_name': 'USBRemoteDevice', '_ormbases': [u'main_app.RemoteDevice']},
            u'remotedevice_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['main_app.RemoteDevice']", 'unique': 'True', 'primary_key': 'True'})
        }
    }

    complete_apps = ['main_app']