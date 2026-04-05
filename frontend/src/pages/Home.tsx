
import "../App.css";
import { Header } from '../components/Header';
import { Algorithms } from "../components/Algorithms";
import React from "react";

const Home: React.FC = () => {
  return (
    <div className="bg-[#2c2c2c] h-screen w-screen grid grid-cols-[70px_300px_1fr_300px_70px] grid-rows-[auto_1fr] gap-0">
      <div className="col-span-5"><Header /></div>

      <div className="bg-[#494949] text-white border-t-[3px] border-r-[3px] border-[#555555]">1</div>
      <Algorithms />
      <div className="bg-[#2c2c2c] text-white border-r-[3px] border-[#555555]">


      </div>
      <div className="bg-[#2c2c2c] text-white border-r-[3px] border-[#555555]">params</div>
      <div className="bg-[#2c2c2c] text-white ">1</div>
    </div>
  )
}

export default Home;