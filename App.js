import React, {useState} from 'react';
import { SafeAreaView, Button, Text, TextInput, View } from 'react-native';

export default function App(){
  const [text, setText] = useState('');
  const [response, setResponse] = useState('');

  async function askText(){
    const form = new FormData();
    form.append('session_id','demo-session');
    form.append('text', text);
    const r = await fetch('http://localhost:8000/ask', {method:'POST', body: form});
    const json = await r.json();
    setResponse(json.text);
  }

  return (
    <SafeAreaView style={{flex:1, padding:20}}>
      <TextInput placeholder='Ask Sales Buddy' value={text} onChangeText={setText} style={{borderWidth:1,padding:8}} />
      <Button title='Ask' onPress={askText} />
      <View style={{marginTop:20}}>
        <Text>Response:</Text>
        <Text>{response}</Text>
      </View>
    </SafeAreaView>
  );
}
