import copy
import json
import unittest
from datetime import datetime, timezone
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
import official_playoffs as o

FIX = Path(__file__).with_name('playoff_test_fixtures.json')
def fixture(name): return json.loads(FIX.read_text())[name]

class BracketTests(unittest.TestCase):
    def setUp(self): self.c = fixture('fcs-2026-selection')
    def test_exact_committee_field_and_paths(self):
        b=o.render(o.parse(self.c,'fcs'))
        self.assertEqual(len(b['field']),24)
        self.assertEqual(b['field'][0]['team'],'Montana State')
        self.assertEqual(b['rounds'][0]['games'][0],['Harvard','Monmouth'])
        self.assertEqual(b['rounds'][1]['games'][0],['Montana State',None])
        self.assertEqual(b['rounds'][1]['games'][4],['Tarleton State',None])
        self.assertIsNone(b['champion'])
    def test_empty_fbs_template_is_not_official(self):
        self.assertIsNone(o.parse(fixture('fbs-2026-unannounced'),'fbs'))
    def test_live_lead_never_advances(self):
        g=self.c['games'][1];g['gameState']='L'
        for i,t in enumerate(g['teams']): t.update(score=35 if i==0 else 14,isWinner=i==0)
        b=o.render(o.parse(self.c,'fcs'))
        self.assertEqual(b['rounds'][1]['games'][0],['Montana State',None])
    def test_final_advances_to_exact_slot(self):
        g=self.c['games'][1];g.update(gameState='F',statusCodeDisplay='final')
        for i,t in enumerate(g['teams']): t.update(score=35 if i==0 else 14,isWinner=i==0)
        b=o.render(o.parse(self.c,'fcs'))
        self.assertEqual(b['rounds'][1]['games'][0],['Montana State','Harvard'])
        self.assertEqual(b['completed_games'],1)
    def test_complete_historical_brackets_and_champions(self):
        for div,champion in [('fcs','Montana State'),('fbs','Indiana')]:
            b=o.render(o.parse(fixture(div+'-2025-final'),div,2025))
            self.assertEqual(b['champion'],champion)
            self.assertEqual(b['completed_games'],23 if div=='fcs' else 11)
            self.assertTrue(all(all(game) for r in b['rounds'] for game in r['games']))
    def test_partial_field_and_wrong_season_rejected(self):
        self.c['games'][1]['teams']=[]
        with self.assertRaises(ValueError):o.parse(self.c,'fcs')
        with self.assertRaises(ValueError):o.parse(fixture('fcs-2025-final'),'fcs')
    def test_invalid_final_rejected(self):
        g=self.c['games'][1];g.update(gameState='F',statusCodeDisplay='final')
        with self.assertRaises(ValueError):o.parse(self.c,'fcs')
    def test_outage_keeps_official_field_and_timestamp(self):
        b=o.parse(self.c,'fcs');b['updated_at']='2026-11-22T20:00:00+00:00'
        def fail(url):raise OSError('temporary outage')
        updated=o.update({'fcs':b},fail,datetime(2026,11,24,tzinfo=timezone.utc))
        self.assertEqual(updated['fcs']['field'],b['field'])
        self.assertEqual(updated['fcs']['updated_at'],b['updated_at'])
        self.assertIn('warning',updated['fcs'])
        self.assertEqual(updated['fbs']['mode'],'projected')
    def test_committee_field_never_mutates_projection_or_scores(self):
        projection={'as_of':'original','fcs':{'field':[]},'fbs':{'field':[]}}
        original=copy.deepcopy(projection)
        b=o.apply(projection,{'fcs':o.parse(self.c,'fcs')})
        self.assertEqual(projection,original)
        self.assertEqual(b['fcs']['mode'],'official');self.assertEqual(b['fbs']['mode'],'projected')
    def test_public_page_decoder(self):
        # The reference table mirrors the public Nuxt serialization, without executing JS.
        values=[{'pinia':1},{'main':2},{'championship':3},['Ref',4],{'season':5},2026]
        html='<script type="application/json" id="__NUXT_DATA__">'+json.dumps(values)+'</script>'
        self.assertEqual(o.championship(html),{'season':2026})

if __name__=='__main__':unittest.main()
