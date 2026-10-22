'use strict';
/* Testomgeving: alle omgevingsafhankelijke waarden staan uitsluitend hier. */
window.OWZ_CONFIG=Object.freeze({
  environment:'test',
  version:'1.1g-test',
  supabase:Object.freeze({
    url:'https://lemcbncvqcsffatsxpdq.supabase.co',
    anonKey:'sb_publishable_xvnpAGVE1Kf3DhO0PDck7g_ck1nix2O'
  }),
  storage:Object.freeze({favoritesKey:'owz_test_favorites'}),
  regulations:Object.freeze([
    {id:'OW',name:'Omgevingswet',bwb:'BWBR0037885',file:'ow_legal_graph.json'},
    {id:'BAL',name:'Besluit activiteiten leefomgeving (BAL)',bwb:'BWBR0041330',file:'bal_legal_graph.json'},
    {id:'BBL',name:'Besluit bouwwerken leefomgeving (BBL)',bwb:'BWBR0041297',file:'bbl_legal_graph.json'},
    {id:'BKL',name:'Besluit kwaliteit leefomgeving (BKL)',bwb:'BWBR0041313',file:'bkl_legal_graph.json'},
    {id:'OB',name:'Omgevingsbesluit (OB)',bwb:'BWBR0041278',file:'ob_legal_graph.json'},
    {id:'OR',name:'Omgevingsregeling (OR)',bwb:'BWBR0045528',file:'or_legal_graph.json'}
  ])
});