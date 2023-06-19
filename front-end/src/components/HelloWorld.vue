<template>
  <div id="app">
    <div class="container">
      <h1>LowBing</h1>
      <form @submit.prevent="aql_handleSubmit">
        <input
          type="text"
          v-model="aql_inputText"
          placeholder="Enter your query in plain English or Chinese, and press submit"
          required
        />
        <button type="submit" :disabled="aql_loading">Submit</button>
      </form>
      <div v-if="aql_loading">Loading...</div>
      <div v-if="news_apiResponse">
        <h2>Headlines</h2>
        <ul>
          <li v-for="story in news_apiResponse.stories" :key="story.id">
            <a :href="story.links.permalink" target="_blank">{{ story.title }}</a> -
            {{ story.source.name }}
          </li>
        </ul>
        <button @click="summary_handleSubmit">Summarize</button>
        <div v-if="summary_loading">Loading...</div>
        <div v-if="summary_apiResponse">
          <h2>Summary</h2>
          <p>{{ summary_apiResponse.summary }}</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios'

export default {
  data() {
    return {
      aql_inputText: '',
      aql_loading: false,
      news_apiResponse: null,
      summary_apiResponse: null,
      summary_loading: false,
      api_url: `http://127.0.0.1:5173/api`
    }
  },
  methods: {
    async aql_handleSubmit() {
      this.aql_loading = true
      this.summary_apiResponse = null
      this.news_apiResponse = null

      try {
        const response = await axios.get(`${this.api_url}/text2aql`, {
          params: {
            text: this.aql_inputText
          }
        })
        const { data } = response
        const parts = data.aql.split('\n')
        const aql = parts[0]
        const params = parts[1]

        const newsResponse = await axios.get(`${this.api_url}/fetchnews`, {
          params: {
            aql,
            params,
            num_articles: 10
          }
        })
        this.news_apiResponse = newsResponse.data
      } catch (error) {
        console.error(error)
      } finally {
        this.aql_loading = false
      }
    },
    async summary_handleSubmit() {
      this.summary_loading = true
      try {
        const headlines = this.news_apiResponse.stories.map(({ title }) => title).join('\\n')
        const response = await axios.get(`${this.api_url}/summarize`, {
          params: {
            headlines,
            num_sentences: 3
          }
        })

        this.summary_apiResponse = response.data
      } catch (error) {
        console.error(error)
      } finally {
        this.summary_loading = false
      }
    }
  }
}
</script>

<style>
#app {
  font-family: Arial, sans-serif;
}

.container {
  width: 800px;
  margin: 0 auto;
}

input[type='text'] {
  width: 100%;
  padding: 12px;
  margin-top: 16px;
  margin-bottom: 16px;
  display: inline-block;
  border: 1px solid #ccc;
  border: 4px;
  box-sizing: border-box;
}

button {
  background-color: #4caf50;
  color: white;
  padding: 10px 20px;
  margin: 8px 0;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

button:hover {
  background-color: #45a049;
}

li {
  margin-bottom: 8px;
}
</style>
