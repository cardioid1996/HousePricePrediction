<template>
  <div id="app">
    <header>
    <HeadNav></HeadNav>
    </header>
    <div style="width:100%;text-align: center;margin:0 auto">
    <router-view/>
    </div>
    <footer style="margin-top: -200;">
			<FootNav></FootNav>
    </footer>

  </div>

</template>

<script>

import HeadNav from './components/HeadNav.vue'
import FootNav from './components/FootNav.vue'
export default {
  components:{
    HeadNav,
		FootNav
  },
	provide(){
		return{
			reload: this.reload
		}
	},
	data(){
		return{
			isRouterAlive: true
		}
	},
	methods:{
		reload(){
			this.isRouterAlive = false
			this.$nextTick(function(){
				this.isRouterAlive = true
			})
		}
	},
  name: 'App'
}


</script>


<style scoped>
#app {
  font-family: 'Avenir', Helvetica, Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  text-align: center;
  color: #2c3e50;
  margin-top: 0px;
}
</style>
