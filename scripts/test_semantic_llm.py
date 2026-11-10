"""HTTP contract tests with a local stub; never counted as cloud experiments."""
import json,threading,unittest,os
from http.server import BaseHTTPRequestHandler,HTTPServer
from unittest.mock import patch
from semantic_llm import JSONPolicy
class ContractTests(unittest.TestCase):
    def test_json_transport_and_validation(self):
        captured=[]
        class Handler(BaseHTTPRequestHandler):
            def do_POST(self):
                request=json.loads(self.rfile.read(int(self.headers['Content-Length'])));captured.append(request)
                obs=json.loads(request['messages'][1]['content'])
                action={'task_id':obs['task_id'],'observation_id':obs['observation_id'],'action':'scan','reason_code':'observe_unknown'}
                body=json.dumps({'choices':[{'message':{'content':json.dumps(action)}}],'usage':{'total_tokens':37}}).encode()
                self.send_response(200);self.end_headers();self.wfile.write(body)
            def log_message(self,*a):pass
        server=HTTPServer(('127.0.0.1',0),Handler);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
        try:
            with patch.dict(os.environ,{'SEMANTIC_TEST_KEY':'local-test'}):
                policy=JSONPolicy('deepseek',{'base_url':'http://127.0.0.1:'+str(server.server_port),'model':'stub-only','key_env':'SEMANTIC_TEST_KEY'})
                obs={'task_id':'test','observation_id':3,'objects':[],'candidates':[],'target':{'category':'pipe','color':'yellow'},'scan_completed':False}
                action,meta=policy.decide(obs)
                self.assertEqual(action['action'],'scan');self.assertEqual(meta['usage']['total_tokens'],37)
                self.assertEqual(captured[0]['response_format'],{'type':'json_object'})
                qwen=JSONPolicy('qwen',{'base_url':'http://127.0.0.1:'+str(server.server_port),'model':'stub-only','key_env':'SEMANTIC_TEST_KEY'},
                                settings={'timeout_s':3,'temperature':.2,'max_tokens':123,'enable_thinking':False})
                action,_=qwen.decide(obs)
                self.assertEqual(action['action'],'scan')
                self.assertEqual(qwen.timeout,3)
                self.assertEqual(captured[-1]['max_tokens'],123)
                self.assertEqual(captured[-1]['temperature'],.2)
                self.assertFalse(captured[-1]['enable_thinking'])
                obs['scan_completed']=True
                obs['objects']=[{'id':'blue','category':'pipe','color':'blue','confirmed':True,'observation_age_s':0}]
                obs['candidates']=[{'id':'wrong','kind':'approach','object_id':'blue','reachable':True},
                                   {'id':'frontier','kind':'explore','reachable':True}]
                # Stub still emits scan; inspect the exact model-facing search contract.
                with self.assertRaisesRegex(ValueError,'action not allowed'):qwen.decide(obs)
                sent=json.loads(captured[-1]['messages'][1]['content'])
                self.assertEqual(sent['allowed_actions'],['explore','hold'])
                self.assertEqual([c['id'] for c in sent['candidates']],['frontier'])
        finally:server.shutdown();server.server_close();thread.join()
    def test_missing_key_fails(self):
        with patch.dict(os.environ,{},clear=True):
            with self.assertRaises(RuntimeError):JSONPolicy('deepseek')

class CredentialsTests(unittest.TestCase):
    def test_env_file_does_not_execute_shell(self):
        import tempfile
        from pathlib import Path
        from semantic_credentials import load_credentials
        with tempfile.TemporaryDirectory() as directory,patch.dict(os.environ,{},clear=True):
            f=Path(directory)/'.env';f.write_text('DEEPSEEK_API_KEY="literal-$(not_a_command)"')
            load_credentials(f)
            self.assertEqual(os.getenv('DEEPSEEK_API_KEY'),'literal-$(not_a_command)')
    def test_reject_unrelated_variables(self):
        import tempfile
        from pathlib import Path
        from semantic_credentials import load_credentials
        with tempfile.TemporaryDirectory() as directory:
            f=Path(directory)/'.env';f.write_text('HOME=wrong')
            with self.assertRaises(ValueError):load_credentials(f)

class TrialCredentialTests(unittest.TestCase):
    def test_rule_launches_with_missing_credential_file(self):
        import tempfile
        from pathlib import Path
        import run_semantic_trial as trial
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            output = root / 'trial'
            argv = ['run_semantic_trial.py', '--policy', 'rule', '--output', str(output)]
            with patch('sys.argv', argv), \
                 patch.dict(os.environ, {'ROV_SEMANTIC_ENV_FILE': str(root / 'missing.env')}), \
                 patch('semantic_credentials.load_credentials') as credentials, \
                 patch.object(trial.subprocess, 'Popen') as launch, \
                 patch.object(trial, 'stop'), patch('builtins.print'):
                launch.return_value.poll.return_value = 0
                trial.main()
                credentials.assert_not_called()
                self.assertEqual(launch.call_count, 3)
                self.assertTrue((output / 'summary.json').exists())
                effective=json.loads((output/'effective_config.json').read_text())
                self.assertEqual(effective['policy'],'rule')
                # Both child processes must consume the frozen runtime settings.
                self.assertTrue((output/'config/runtime.json').exists())
                env=launch.call_args_list[0].kwargs['env']
                self.assertEqual(env['ROV_SEMANTIC_RUNTIME_CONFIG'],str(output/'config/runtime.json'))
                from experiment import load_experiment
                with patch.dict(os.environ,env):
                    self.assertEqual(load_experiment('platform_semantic')['hydrodynamics']['component_model_file'],
                                     'config/hydrodynamic_components/bluerov_mesh.json')

    def test_cloud_missing_file_fails_before_launch(self):
        import tempfile
        from pathlib import Path
        import run_semantic_trial as trial
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            output = root / 'trial'
            argv = ['run_semantic_trial.py', '--policy', 'deepseek', '--output', str(output)]
            with patch('sys.argv', argv), \
                 patch.dict(os.environ, {'ROV_SEMANTIC_ENV_FILE': str(root / 'missing.env')}), \
                 patch.object(trial.subprocess, 'Popen') as launch:
                with self.assertRaises(FileNotFoundError):
                    trial.main()
                launch.assert_not_called()
                self.assertFalse(output.exists())

if __name__ == '__main__':
    unittest.main()
